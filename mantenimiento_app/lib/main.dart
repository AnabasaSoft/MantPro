import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:image_painter/image_painter.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;

void main() => runApp(const MaterialApp(home: MainScreen(), debugShowCheckedModeBanner: false));

// ==========================================
// 1. MODELOS DE DATOS
// ==========================================
class Registro {
  String titulo, detalles, tags;
  String? imagePath;
  Registro({required this.titulo, required this.detalles, required this.tags, this.imagePath});

  Map<String, dynamic> toJson() => {'titulo': titulo, 'detalles': detalles, 'tags': tags, 'imagePath': imagePath};
  factory Registro.fromJson(Map<String, dynamic> json) => Registro(titulo: json['titulo'], detalles: json['detalles'], tags: json['tags'], imagePath: json['imagePath']);
}

class PendientePC {
  int id;
  String titulo, detalles;
  PendientePC({required this.id, required this.titulo, required this.detalles});
  factory PendientePC.fromJson(Map<String, dynamic> json) => PendientePC(id: json['id'], titulo: json['titulo'], detalles: json['detalles']);
}

// ==========================================
// 2. PANTALLA PRINCIPAL
// ==========================================
class MainScreen extends StatefulWidget {
  const MainScreen({super.key});
  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _indiceActual = 0;
  final List<Widget> _pantallas = [const TabMisRegistros(), const TabPendientesPC()];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _indiceActual, children: _pantallas),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _indiceActual,
        onTap: (index) => setState(() => _indiceActual = index),
        backgroundColor: Colors.blueGrey,
        selectedItemColor: Colors.white,
        unselectedItemColor: Colors.white60,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.folder), label: "Mis Registros"),
          BottomNavigationBarItem(icon: Icon(Icons.list_alt), label: "Trabajos Pendientes"),
        ],
      ),
    );
  }
}

// ==========================================
// 3. PESTAÑA 1: MIS REGISTROS (LOCALES)
// ==========================================
class TabMisRegistros extends StatefulWidget {
  const TabMisRegistros({super.key});
  @override
  State<TabMisRegistros> createState() => _TabMisRegistrosState();
}

class _TabMisRegistrosState extends State<TabMisRegistros> {
  List<Registro> _pendientes = [];
  bool _cargando = false;
  String? _urlPC;

  @override
  void initState() {
    super.initState();
    _inicializar();
  }

  Future<void> _inicializar() async {
    final prefs = await SharedPreferences.getInstance();
    final String? datosJson = prefs.getString('registros_pendientes');
    if (datosJson != null) {
      final List<dynamic> l = json.decode(datosJson);
      setState(() => _pendientes = l.map((item) => Registro.fromJson(item)).toList());
    }
    setState(() => _urlPC = prefs.getString('pc_ip_url'));
    if (_pendientes.isNotEmpty && _urlPC != null) _sincronizar();
  }

  Future<void> _guardarDatos() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('registros_pendientes', json.encode(_pendientes.map((r) => r.toJson()).toList()));
  }

  void _addRegistro(Registro r) { setState(() => _pendientes.add(r)); _guardarDatos(); }
  void _borrarRegistro(int i) { setState(() => _pendientes.removeAt(i)); _guardarDatos(); }
  void _editarRegistro(int index, Registro r) { setState(() => _pendientes[index] = r); _guardarDatos(); }

  Future<void> _confirmarBorrado(int index) async {
    final bool? confirmar = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("¿Borrar?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("CANCELAR")),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text("BORRAR", style: TextStyle(color: Colors.red))),
        ],
      ),
    );
    if (confirmar == true) _borrarRegistro(index);
  }

  Future<void> _sincronizar([String? nuevaUrl]) async {
    final prefs = await SharedPreferences.getInstance();
    String? urlUsar = nuevaUrl ?? _urlPC;
    if (urlUsar == null) return;
    if (nuevaUrl != null) {
      await prefs.setString('pc_ip_url', nuevaUrl);
      setState(() => _urlPC = nuevaUrl);
    }

    setState(() => _cargando = true);
    final uri = Uri.parse("$urlUsar/api/upload");
    List<Registro> enviados = [];

    for (var item in _pendientes) {
      try {
        var req = http.MultipartRequest('POST', uri);
        req.fields['titulo'] = item.titulo; req.fields['detalles'] = item.detalles; req.fields['tags'] = item.tags;
        if (item.imagePath != null && File(item.imagePath!).existsSync()) {
          req.files.add(await http.MultipartFile.fromPath('foto', item.imagePath!));
        }
        var res = await req.send();
        if (res.statusCode == 200) enviados.add(item);
      } catch (e) { /* Error */ }
    }

    if (mounted) {
      setState(() => _cargando = false);
      if (enviados.isNotEmpty) {
        setState(() { for (var e in enviados) _pendientes.remove(e); });
        _guardarDatos();
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("✅ ${enviados.length} enviados")));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis Registros'), backgroundColor: Colors.blueGrey,
        actions: [
          // BOTÓN DE RECONECTAR (SIEMPRE VISIBLE)
          IconButton(
            icon: const Icon(Icons.qr_code),
            tooltip: "Cambiar PC",
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => QrScanScreen(onScan: _sincronizar)))
          ),
          // BOTÓN DE SYNC (SOLO SI YA HAY IP)
          if (_urlPC != null)
            IconButton(
              icon: _cargando ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white)) : const Icon(Icons.sync),
              onPressed: () => _sincronizar()
            )
        ],
      ),
      body: _pendientes.isEmpty
      ? const Center(child: Text("Sin registros locales", style: TextStyle(color: Colors.grey)))
      : ListView.builder(
        itemCount: _pendientes.length,
        itemBuilder: (ctx, i) {
          final item = _pendientes[i];
          File? f = item.imagePath != null ? File(item.imagePath!) : null;
          return Card(
            child: ListTile(
              leading: f != null && f.existsSync() ? Image.file(f, width: 40, height: 40, fit: BoxFit.cover) : const Icon(Icons.build),
              title: Text(item.titulo, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text(item.detalles, maxLines: 1),
              trailing: IconButton(icon: const Icon(Icons.delete, color: Colors.red), onPressed: () => _confirmarBorrado(i)),
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(onSave: (r) => _editarRegistro(i, r), registroExistente: item))),
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(child: const Icon(Icons.add), onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(onSave: _addRegistro)))),
    );
  }
}

// ==========================================
// 4. PESTAÑA 2: TRABAJOS PENDIENTES PC
// ==========================================
class TabPendientesPC extends StatefulWidget {
  const TabPendientesPC({super.key});
  @override
  State<TabPendientesPC> createState() => _TabPendientesPCState();
}

class _TabPendientesPCState extends State<TabPendientesPC> {
  List<PendientePC> _listaPC = [];

  List<Map<String, dynamic>> _colaSalida = [];
  List<Map<String, dynamic>> _colaNuevos = [];
  List<Map<String, dynamic>> _colaEdicion = [];
  List<int> _colaBorrados = [];

  Map<String, String> _fotosLocales = {};

  bool _cargando = false;
  String? _urlPC;

  @override
  void initState() {
    super.initState();
    _cargarCache();
  }

  Future<void> _cargarCache() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _urlPC = prefs.getString('pc_ip_url');

      String? l = prefs.getString('trabajos_pc');
      if (l != null) _listaPC = (json.decode(l) as List).map((i) => PendientePC.fromJson(i)).toList();

      String? c = prefs.getString('cola_salida');
      if (c != null) _colaSalida = List<Map<String, dynamic>>.from(json.decode(c));

      String? n = prefs.getString('cola_nuevos');
      if (n != null) _colaNuevos = List<Map<String, dynamic>>.from(json.decode(n));

      String? e = prefs.getString('cola_edicion');
      if (e != null) _colaEdicion = List<Map<String, dynamic>>.from(json.decode(e));

      String? b = prefs.getString('cola_borrados');
      if (b != null) _colaBorrados = List<int>.from(json.decode(b));

      String? f = prefs.getString('fotos_locales_map');
      if (f != null) _fotosLocales = Map<String, String>.from(json.decode(f));
    });

      if (_urlPC != null) _sincronizarTodo(silencioso: true);
  }

  Future<void> _guardarCache() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('trabajos_pc', json.encode(_listaPC.map((p) => {'id': p.id, 'titulo': p.titulo, 'detalles': p.detalles}).toList()));
    await prefs.setString('cola_salida', json.encode(_colaSalida));
    await prefs.setString('cola_nuevos', json.encode(_colaNuevos));
    await prefs.setString('cola_edicion', json.encode(_colaEdicion));
    await prefs.setString('cola_borrados', json.encode(_colaBorrados));
    await prefs.setString('fotos_locales_map', json.encode(_fotosLocales));
  }

  Future<void> _sincronizarTodo({bool silencioso = false}) async {
    if (_urlPC == null) return;
    if (!silencioso) setState(() => _cargando = true);

    List<int> borradosOk = [];
    for (var id in _colaBorrados) { if (await _apiPost('eliminar_pendiente', {'id': id.toString()})) borradosOk.add(id); }
    if (borradosOk.isNotEmpty) setState(() { for (var id in borradosOk) _colaBorrados.remove(id); });

    List<Map<String, dynamic>> nuevosOk = [];
    for (var t in _colaNuevos) { if (await _apiMultipart('agregar_pendiente', t)) nuevosOk.add(t); }
    if (nuevosOk.isNotEmpty) setState(() { for (var t in nuevosOk) _colaNuevos.remove(t); });

    List<Map<String, dynamic>> edicionOk = [];
    for (var t in _colaEdicion) { if (await _apiMultipart('editar_pendiente', t)) edicionOk.add(t); }
    if (edicionOk.isNotEmpty) setState(() { for (var t in edicionOk) _colaEdicion.remove(t); });

    List<Map<String, dynamic>> salidaOk = [];
    for (var t in _colaSalida) { if (await _apiMultipart('completar_pendiente', t)) salidaOk.add(t); }
    if (salidaOk.isNotEmpty) setState(() { for (var t in salidaOk) _colaSalida.remove(t); });

    await _guardarCache();

    try {
      final res = await http.get(Uri.parse("$_urlPC/api/pendientes"));
      if (res.statusCode == 200) {
        final List<dynamic> datos = json.decode(res.body);
        setState(() => _listaPC = datos.map((item) => PendientePC.fromJson(item)).toList());
        await _guardarCache();
      }
    } catch (e) {}

    if (!silencioso && mounted) setState(() => _cargando = false);
  }

  Future<bool> _apiPost(String endpoint, Map<String, String> body) async {
    try { return (await http.post(Uri.parse("$_urlPC/api/$endpoint"), body: body)).statusCode == 200; } catch (e) { return false; }
  }
  Future<bool> _apiMultipart(String endpoint, Map<String, dynamic> datos) async {
    try {
      var req = http.MultipartRequest('POST', Uri.parse("$_urlPC/api/$endpoint"));
      if (datos.containsKey('id')) req.fields['id'] = datos['id'].toString();
      req.fields['titulo'] = datos['titulo']; req.fields['detalles'] = datos['detalles'];
      if (datos.containsKey('tags')) req.fields['tags'] = datos['tags'];
      if (datos['imagePath'] != null && File(datos['imagePath']).existsSync()) {
        req.files.add(await http.MultipartFile.fromPath('foto', datos['imagePath']));
      }
      return (await req.send()).statusCode == 200;
    } catch (e) { return false; }
  }

  // --- LÓGICA DE GESTIÓN (TÉCNICA MATRÍCULA) ---

  String? _extraerRef(String texto) {
    final match = RegExp(r"\[REF:(\d+)\]").firstMatch(texto);
    return match?.group(1);
  }

  void _abrirGestionar(PendientePC p) {
    String? refID = _extraerRef(p.detalles);
    String? fotoLocal;

    if (refID != null && _fotosLocales.containsKey(refID)) {
      fotoLocal = _fotosLocales[refID];
    } else if (_fotosLocales.containsKey(p.id.toString())) {
      fotoLocal = _fotosLocales[p.id.toString()];
    }

    if (fotoLocal != null && !File(fotoLocal).existsSync()) fotoLocal = null;

    Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(
      pendientePC: p,
      fotoInicialPath: fotoLocal,

      onSave: (registro) { // TERMINAR
        Map<String, dynamic> t = {'id': p.id, 'titulo': registro.titulo, 'detalles': registro.detalles, 'tags': registro.tags, 'imagePath': registro.imagePath};
        setState(() {
          _colaSalida.add(t);
          _listaPC.removeWhere((i) => i.id == p.id);
          if (refID != null) _fotosLocales.remove(refID);
          _fotosLocales.remove(p.id.toString());
        });
        _guardarCache(); _sincronizarTodo(silencioso: true);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Finalizado")));
      },

      onUpdate: (registro) { // ACTUALIZAR
        String clave = refID ?? p.id.toString();

        if (registro.imagePath != null) {
          setState(() => _fotosLocales[clave] = registro.imagePath!);
        }

        Map<String, dynamic> t = {'id': p.id, 'titulo': registro.titulo, 'detalles': registro.detalles, 'imagePath': registro.imagePath};
        setState(() => _colaEdicion.add(t));
        _guardarCache();
        _sincronizarTodo(silencioso: true);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Guardado")));
        Navigator.pop(context);
      }
    )));
  }

  void _borrar(int id) async {
    if (await showDialog(context: context, builder: (ctx) => AlertDialog(title:const Text("¿Borrar?"), actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false), child:const Text("NO")), TextButton(onPressed:()=>Navigator.pop(ctx,true), child:const Text("SÍ"))])) == true) {
      setState(() {
        _listaPC.removeWhere((p) => p.id == id);
        _colaBorrados.add(id);
      });
      _guardarCache(); _sincronizarTodo(silencioso: true);
    }
  }

  Future<void> _escanearQR() async {
    Navigator.push(context, MaterialPageRoute(builder: (_) => QrScanScreen(onScan: (codigo) async {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('pc_ip_url', codigo);
      setState(() => _urlPC = codigo);
      _sincronizarTodo();
    })));
  }

  @override
  Widget build(BuildContext context) {
    int cola = _colaSalida.length + _colaNuevos.length + _colaBorrados.length + _colaEdicion.length;

    return Scaffold(
      appBar: AppBar(
        title: Text(_urlPC == null ? "Offline" : "Trab. Pend. (${cola > 0 ? '⬆$cola' : 'OK'})"),
        backgroundColor: cola > 0 ? Colors.orange[800] : Colors.blueGrey,
        actions: [
          // BOTÓN RECONECTAR (SIEMPRE)
          IconButton(
            icon: const Icon(Icons.qr_code),
            tooltip: "Cambiar PC",
            onPressed: _escanearQR
          ),
          // BOTÓN SYNC
          IconButton(
            icon: _cargando ? const SizedBox(width:20,height:20,child:CircularProgressIndicator(color:Colors.white)) : const Icon(Icons.sync),
            onPressed: () => _sincronizarTodo()
          )
        ],
      ),
      body: _urlPC == null
      ? Center(child: ElevatedButton.icon(icon: const Icon(Icons.qr_code), label: const Text("Vincular PC"), onPressed: _escanearQR))
      : _listaPC.isEmpty ? const Center(child: Text("No hay tareas"))
      : ListView.builder(
        itemCount: _listaPC.length,
        itemBuilder: (ctx, i) {
          final item = _listaPC[i];

          String? refID = _extraerRef(item.detalles);
          bool tieneFoto = false;
          String? pathFoto;

          if (refID != null && _fotosLocales.containsKey(refID)) pathFoto = _fotosLocales[refID];
          else if (_fotosLocales.containsKey(item.id.toString())) pathFoto = _fotosLocales[item.id.toString()];

          if (pathFoto != null && File(pathFoto).existsSync()) tieneFoto = true;

          String limpio = item.detalles.replaceAll(RegExp(r"\[FOTO:.*?\]"), "").replaceAll(RegExp(r"\[REF:.*?\]"), "").trim();

          return Card(
            child: ListTile(
              leading: tieneFoto
              ? ClipRRect(borderRadius: BorderRadius.circular(4), child: Image.file(File(pathFoto!), width: 50, height: 50, fit: BoxFit.cover))
              : const CircleAvatar(backgroundColor: Colors.orange, child: Icon(Icons.warning_amber, color: Colors.white)),
              title: Text(item.titulo, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text(limpio, maxLines: 2),
              onTap: () => _abrirGestionar(item),
              trailing: IconButton(icon: const Icon(Icons.delete, color: Colors.red), onPressed: () => _borrar(item.id)),
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: Colors.orange[800], icon: const Icon(Icons.add_task), label: const Text("AÑADIR"),
        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(esCrearPendiente: true, onSave: (r) {

          String refUnica = DateTime.now().millisecondsSinceEpoch.toString();

          if (r.imagePath != null) {
            setState(() => _fotosLocales[refUnica] = r.imagePath!);
          }

          String detallesConRef = "${r.detalles} [REF:$refUnica]";

          Map<String, dynamic> t = {'titulo': r.titulo, 'detalles': detallesConRef, 'imagePath': r.imagePath};
          setState(() => _colaNuevos.add(t));

          PendientePC temp = PendientePC(id: -DateTime.now().millisecondsSinceEpoch, titulo: r.titulo, detalles: detallesConRef);
          setState(() => _listaPC.insert(0, temp));

          _guardarCache();
          _sincronizarTodo(silencioso: true);

          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Pendiente creado")));
        }))),
      ),
    );
  }
}

// ==========================================
// 5. FORMULARIO UNIFICADO
// ==========================================
class FormScreen extends StatefulWidget {
  final Function(Registro) onSave;
  final Function(Registro)? onUpdate;
  final PendientePC? pendientePC;
  final Registro? registroExistente;
  final bool esCrearPendiente;
  final String? fotoInicialPath;

  const FormScreen({
    super.key, required this.onSave, this.onUpdate,
    this.pendientePC, this.registroExistente, this.esCrearPendiente = false, this.fotoInicialPath,
  });

  @override
  State<FormScreen> createState() => _FormScreenState();
}

class _FormScreenState extends State<FormScreen> {
  final _titleCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  final _tagCtrl = TextEditingController();
  String? _imagePath;
  bool _isUrgente=false, _isElectrico=false, _isMecanico=false, _isPreventivo=false;

  @override
  void initState() {
    super.initState();
    if (widget.pendientePC != null) {
      _titleCtrl.text = widget.pendientePC!.titulo;
      _descCtrl.text = widget.pendientePC!.detalles.replaceAll(RegExp(r"\[FOTO:.*?\]"), "").replaceAll(RegExp(r"\[REF:.*?\]"), "").trim();
      if (widget.fotoInicialPath != null) _imagePath = widget.fotoInicialPath;
    }
    if (widget.registroExistente != null) {
      final r = widget.registroExistente!;
      if (r.titulo.isNotEmpty) _titleCtrl.text = r.titulo;
      if (r.detalles.isNotEmpty) _descCtrl.text = r.detalles;
      if (r.imagePath != null && File(r.imagePath!).existsSync()) _imagePath = r.imagePath;
      if (r.tags.contains("Urgente")) _isUrgente=true;
      if (r.tags.contains("Eléctrico")) _isElectrico=true;
      if (r.tags.contains("Mecánico")) _isMecanico=true;
      if (r.tags.contains("Preventivo")) _isPreventivo=true;
    }
  }

  Future<void> _takePhoto() async {
    try {
      final picker = ImagePicker();
      final pickedFile = await picker.pickImage(source: ImageSource.camera, imageQuality: 60);
      if (pickedFile != null) {
        final directory = await getApplicationDocumentsDirectory();
        final String fileName = 'foto_${DateTime.now().millisecondsSinceEpoch}.jpg';
        final String nuevoPath = path.join(directory.path, fileName);
        await File(pickedFile.path).copy(nuevoPath);
        setState(() { _imagePath = nuevoPath; });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("❌ Error: $e")));
    }
  }

  Future<void> _openEditor() async {
    if (_imagePath == null) return;
    final bool? ok = await Navigator.push(context, MaterialPageRoute(builder: (_) => ImageEditorScreen(imageFile: File(_imagePath!))));
    if (ok == true) setState(() { PaintingBinding.instance.imageCache.clear(); PaintingBinding.instance.imageCache.clearLiveImages(); });
  }

  void _borrarFoto() { setState(() { _imagePath = null; }); }

  void _guardarLocal(bool esTerminar) {
    if (_titleCtrl.text.isEmpty) return;
    List<String> l = [];
    if (_isUrgente) l.add("Urgente"); if (_isElectrico) l.add("Eléctrico");
    if (_isMecanico) l.add("Mecánico"); if (_isPreventivo) l.add("Preventivo");
    if (_tagCtrl.text.isNotEmpty) l.add(_tagCtrl.text);

    String detallesFinales = _descCtrl.text;
    if (widget.pendientePC != null) {
      final match = RegExp(r"\[REF:(\d+)\]").firstMatch(widget.pendientePC!.detalles);
      if (match != null) {
        detallesFinales += " ${match.group(0)}";
      }
    }

    Registro r = Registro(titulo: _titleCtrl.text, detalles: detallesFinales, tags: l.join(", "), imagePath: _imagePath);

    if (esTerminar) widget.onSave(r);
    else if (widget.onUpdate != null) widget.onUpdate!(r);
    else widget.onSave(r);

    if (widget.onUpdate == null || esTerminar) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    bool esTrabajoPC = widget.pendientePC != null;
    return Scaffold(
      appBar: AppBar(title: Text(esTrabajoPC ? "Gestionar Trabajo" : "Nuevo"), backgroundColor: Colors.blueGrey),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          TextField(controller: _titleCtrl, decoration: const InputDecoration(labelText: "Título")),
          const SizedBox(height: 15),
          TextField(controller: _descCtrl, maxLines: 5, decoration: const InputDecoration(labelText: "Detalles")),
          const SizedBox(height: 15),

          if (!widget.esCrearPendiente) ...[
            CheckboxListTile(title: const Text("🚨 Urgente"), value: _isUrgente, dense:true, onChanged: (v)=>setState(()=>_isUrgente=v!)),
            CheckboxListTile(title: const Text("⚡ Eléctrico"), value: _isElectrico, dense:true, onChanged: (v)=>setState(()=>_isElectrico=v!)),
            CheckboxListTile(title: const Text("⚙️ Mecánico"), value: _isMecanico, dense:true, onChanged: (v)=>setState(()=>_isMecanico=v!)),
            const Divider(),
          ],

          if (_imagePath != null) ...[
            SizedBox(height: 300, child: Image.file(File(_imagePath!), fit: BoxFit.contain)),
            const SizedBox(height: 10),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              ElevatedButton.icon(icon: const Icon(Icons.edit), label: const Text("DIBUJAR"), onPressed: _openEditor),
              const SizedBox(width: 10),
              ElevatedButton.icon(icon: const Icon(Icons.delete), label: const Text("BORRAR"), style: ElevatedButton.styleFrom(backgroundColor:Colors.red), onPressed: _borrarFoto),
            ])
          ] else
          ElevatedButton.icon(icon: const Icon(Icons.camera_alt), label: const Text("AÑADIR FOTO"), style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)), onPressed: _takePhoto),

          const SizedBox(height: 20),

          if (esTrabajoPC) ...[
            Row(children: [
              Expanded(child: ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.blue, padding: const EdgeInsets.symmetric(vertical: 15)),
                onPressed: () => _guardarLocal(false),
                child: const Text("ACTUALIZAR", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              )),
              const SizedBox(width: 10),
              Expanded(child: ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.green, padding: const EdgeInsets.symmetric(vertical: 15)),
                onPressed: () => _guardarLocal(true),
                child: const Text("TERMINAR", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              )),
            ])
          ] else
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.blueGrey, minimumSize: const Size.fromHeight(50)),
            onPressed: () => _guardarLocal(true),
            child: Text(widget.esCrearPendiente ? "GUARDAR PENDIENTE" : "GUARDAR", style: const TextStyle(fontWeight: FontWeight.bold)),
          )
        ]),
      ),
    );
  }
}

// ==========================================
// 6. UTILIDADES
// ==========================================
class QrScanScreen extends StatefulWidget { final Function(String) onScan; const QrScanScreen({super.key, required this.onScan}); @override State<QrScanScreen> createState() => _S(); }
class _S extends State<QrScanScreen> { bool s=false; @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text("QR PC")),body:MobileScanner(onDetect:(c){if(s)return;if(c.barcodes.isNotEmpty){setState(()=>s=true);widget.onScan(c.barcodes.first.rawValue!);Navigator.pop(context);}}));}

class ImageEditorScreen extends StatefulWidget { final File imageFile; const ImageEditorScreen({super.key, required this.imageFile}); @override State<ImageEditorScreen> createState() => _I(); }
class _I extends State<ImageEditorScreen> { final _c = ImagePainterController(color: Colors.red, strokeWidth: 4.0, mode: PaintMode.freeStyle); bool _g=false; @override void initState(){super.initState();SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp,DeviceOrientation.portraitDown]);} @override void dispose(){SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp,DeviceOrientation.portraitDown,DeviceOrientation.landscapeLeft,DeviceOrientation.landscapeRight]);super.dispose();} @override Widget build(BuildContext context)=>WillPopScope(onWillPop:()async=>!_g,child:Scaffold(backgroundColor:Colors.black,appBar:AppBar(backgroundColor:Colors.black,leading:_g?const SizedBox():const BackButton(color:Colors.white),title:Text(_g?"Guardando...":"Dibujar",style:const TextStyle(color:Colors.white)),actions:[if(_g)const Padding(padding:EdgeInsets.all(16),child:SizedBox(width:24,height:24,child:CircularProgressIndicator(color:Colors.greenAccent)))else IconButton(icon:const Icon(Icons.check,color:Colors.greenAccent,size:30),onPressed:()async{if(_g)return;setState(()=>_g=true);try{var b=await _c.exportImage();if(b!=null){await widget.imageFile.writeAsBytes(b);if(mounted)Navigator.pop(context,true);}}catch(e){}if(mounted)setState(()=>_g=false);})]),body:_g?const Center(child:CircularProgressIndicator(color:Colors.greenAccent)):ImagePainter.file(widget.imageFile,controller:_c,scalable:true)));}
