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

// --- GESTOR DE TEMA GLOBAL ---
final ValueNotifier<ThemeMode> themeNotifier = ValueNotifier(ThemeMode.dark);

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final bool isDark = prefs.getBool('is_dark_mode') ?? true;
  themeNotifier.value = isDark ? ThemeMode.dark : ThemeMode.light;
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: themeNotifier,
      builder: (_, mode, __) {
        return MaterialApp(
          home: const MainScreen(),
          debugShowCheckedModeBanner: false,
          title: "MantPro Móvil",
          themeMode: mode,
          theme: ThemeData.light().copyWith(
            scaffoldBackgroundColor: const Color(0xFFF5F5F5),
            appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF37474F), foregroundColor: Colors.white),
            cardColor: Colors.white,
            colorScheme: const ColorScheme.light(primary: Color(0xFF37474F), secondary: Colors.orangeAccent),
            bottomNavigationBarTheme: const BottomNavigationBarThemeData(backgroundColor: Color(0xFF37474F), selectedItemColor: Colors.white, unselectedItemColor: Colors.white60),
          ),
          darkTheme: ThemeData.dark().copyWith(
            scaffoldBackgroundColor: const Color(0xFF121212),
            appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF1F1F1F), foregroundColor: Colors.white),
            cardColor: const Color(0xFF2C2C2C),
            dividerColor: Colors.grey[700],
            colorScheme: const ColorScheme.dark(primary: Color(0xFF90CAF9), secondary: Colors.orangeAccent, surface: Color(0xFF2C2C2C)),
            bottomNavigationBarTheme: const BottomNavigationBarThemeData(backgroundColor: Color(0xFF1F1F1F), selectedItemColor: Color(0xFF90CAF9), unselectedItemColor: Colors.grey),
          ),
        );
      },
    );
  }
}

// ==========================================
// 1. MODELOS DE DATOS
// ==========================================
class Registro {
  int? id;
  String titulo, detalles, tags;
  String? imagePath;
  String? serverImageName;
  String? fecha; // <--- NUEVO CAMPO

  Registro({
    this.id,
    required this.titulo,
    required this.detalles,
    required this.tags,
    this.imagePath,
    this.serverImageName,
    this.fecha // <--- AÑADIR AL CONSTRUCTOR
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'titulo': titulo,
    'detalles': detalles,
    'tags': tags,
    'imagePath': imagePath,
    'serverImageName': serverImageName,
    'fecha': fecha // <--- AÑADIR A JSON
  };

  factory Registro.fromJson(Map<String, dynamic> json) => Registro(
    id: json['id'],
    titulo: json['titulo'],
    detalles: json['detalles'],
    tags: json['tags'],
    imagePath: json['imagePath'],
    serverImageName: json['serverImageName'],
    fecha: json['fecha'] // <--- LEER DE JSON
  );
}

class PendientePC {
  int id;
  String titulo, detalles;
  PendientePC({required this.id, required this.titulo, required this.detalles});
  factory PendientePC.fromJson(Map<String, dynamic> json) => PendientePC(id: json['id'], titulo: json['titulo'], detalles: json['detalles']);
}

class AvisoPC {
  int id;
  String titulo, frecuencia, rango, estado, color;
  AvisoPC({required this.id, required this.titulo, required this.frecuencia, required this.rango, required this.estado, required this.color});
  factory AvisoPC.fromJson(Map<String, dynamic> json) => AvisoPC(id: json['id'], titulo: json['titulo'], frecuencia: json['frecuencia'], rango: json['rango'], estado: json['estado'], color: json['color']);
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
  void _irAPestana(int index) => setState(() => _indiceActual = index);
  late final List<Widget> _pantallas;

  @override
  void initState() {
    super.initState();
    _pantallas = [
      TabDashboard(onNavigate: _irAPestana),
      const TabMisRegistros(),
      const TabPendientesPC(),
      const TabAvisos(),
      const TabHistorial(),
    ];
  }

  void _toggleTheme() async {
    final prefs = await SharedPreferences.getInstance();
    bool nuevoModo = themeNotifier.value != ThemeMode.dark;
    themeNotifier.value = nuevoModo ? ThemeMode.dark : ThemeMode.light;
    await prefs.setBool('is_dark_mode', nuevoModo);
  }

  @override
  Widget build(BuildContext context) {
    bool isDark = Theme.of(context).brightness == Brightness.dark;
    String titulo = ["Dashboard", "Mis Registros Locales", "Pendientes", "Avisos Recurrentes", "Historial Completo"][_indiceActual];
    return PopScope(
      canPop: _indiceActual == 0,
      onPopInvoked: (didPop) { if (!didPop) _irAPestana(0); },
      child: Scaffold(
        appBar: AppBar(title: Text(titulo), actions: [IconButton(icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode), onPressed: _toggleTheme)]),
        body: IndexedStack(index: _indiceActual, children: _pantallas),
        bottomNavigationBar: BottomNavigationBar(
          currentIndex: _indiceActual,
          type: BottomNavigationBarType.fixed,
          onTap: (index) => setState(() => _indiceActual = index),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: "Inicio"),
            BottomNavigationBarItem(icon: Icon(Icons.edit_note), label: "Local"),
            BottomNavigationBarItem(icon: Icon(Icons.checklist), label: "Pendientes"),
            BottomNavigationBarItem(icon: Icon(Icons.warning_amber), label: "Avisos"),
            BottomNavigationBarItem(icon: Icon(Icons.history), label: "Historial"),
          ],
        ),
      ),
    );
  }
}

// ==========================================
// PESTAÑA 0: DASHBOARD
// ==========================================
class TabDashboard extends StatefulWidget {
  final Function(int) onNavigate;
  const TabDashboard({super.key, required this.onNavigate});
  @override
  State<TabDashboard> createState() => _TabDashboardState();
}

class _TabDashboardState extends State<TabDashboard> {
  Map<String, dynamic> _stats = {"pendientes": 0, "registros_mes": 0, "avisos_total": 0};
  bool _cargando = false;
  String? _urlPC;
  bool _conexionActiva = false;

  @override
  void initState() {
    super.initState();
    _inicializarDatos();
  }

  Future<void> _inicializarDatos() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() => _urlPC = prefs.getString('pc_ip_url'));
    String? cache = prefs.getString('dashboard_cache');
    if (cache != null) setState(() => _stats = json.decode(cache));
    if (_urlPC != null) _cargarStatsOnline();
  }

  Future<void> _cargarStatsOnline() async {
    if (!mounted) return;
    setState(() { _cargando = true; _conexionActiva = false; });
    try {
      final res = await http.get(Uri.parse("http://$_urlPC/api/dashboard")).timeout(const Duration(seconds: 3));
      if (res.statusCode == 200) {
        setState(() { _stats = json.decode(res.body); _conexionActiva = true; });
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('dashboard_cache', res.body);
      }
    } catch (e) { setState(() => _conexionActiva = false); }
    finally { if (mounted) setState(() => _cargando = false); }
  }

  Future<void> _intentarReconexion() async {
    if (_urlPC == null) { _abrirQR(); return; }
    setState(() => _cargando = true);
    try {
      final res = await http.get(Uri.parse("http://$_urlPC/api/dashboard")).timeout(const Duration(seconds: 3));
      if (res.statusCode == 200) {
        setState(() { _stats = json.decode(res.body); _conexionActiva = true; _cargando = false; });
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Conexión recuperada."), duration: Duration(seconds: 2)));
      } else { throw Exception("Err"); }
    } catch (e) {
      setState(() => _cargando = false);
      _abrirQR();
    }
  }

  Future<void> _abrirQR() async {
    final ip = await Navigator.push(context, MaterialPageRoute(builder: (_) => const QRScanScreen()));
    if (ip != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('pc_ip_url', ip);
      _inicializarDatos();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("✅ Vinculado a $ip")));
    }
  }

  Widget _buildCard(String title, String count, IconData icon, Color color, {int? targetTabIndex, VoidCallback? customAction}) {
    return Card(
      elevation: 4, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () { if (customAction != null) customAction(); else if (targetTabIndex != null) widget.onNavigate(targetTabIndex); },
        child: Padding(padding: const EdgeInsets.all(16.0), child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(icon, size: 40, color: color), const SizedBox(height: 10),
          Flexible(child: FittedBox(fit: BoxFit.scaleDown, child: Text(count, style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color)))),
          const SizedBox(height: 5), Text(title, style: const TextStyle(fontSize: 14, color: Colors.grey), textAlign: TextAlign.center),
        ])),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_urlPC == null && _stats['pendientes'] == 0) {
      return Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        const Icon(Icons.link_off, size: 64, color: Colors.grey), const SizedBox(height: 16),
        const Text("PC No Vinculado"), TextButton(onPressed: _abrirQR, child: const Text("Vincular Ahora"))
      ]));
    }
    String txt = _cargando ? "..." : (_urlPC == null ? "Sin IP" : (_conexionActiva ? "Online" : "Reconectar"));
    Color col = _cargando ? Colors.orange : (_urlPC == null ? Colors.grey : (_conexionActiva ? Colors.green : Colors.red));
    return RefreshIndicator(
      onRefresh: _cargarStatsOnline,
      child: ListView(padding: const EdgeInsets.all(16), children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text("Estado Planta", style: Theme.of(context).textTheme.headlineSmall),
          Icon(_conexionActiva ? Icons.cloud_done : Icons.cloud_off, size: 18, color: _conexionActiva ? Colors.green : Colors.red)
        ]), const SizedBox(height: 20),
        GridView.count(crossAxisCount: 2, shrinkWrap: true, crossAxisSpacing: 10, mainAxisSpacing: 10, physics: const NeverScrollableScrollPhysics(), children: [
          _buildCard("Pendientes", "${_stats['pendientes']}", Icons.assignment_late, Colors.orange, targetTabIndex: 2),
          _buildCard("Registros Mes", "${_stats['registros_mes']}", Icons.calendar_today, Colors.blue, targetTabIndex: 4),
          _buildCard("Avisos Config.", "${_stats['avisos_total']}", Icons.alarm, Colors.purple, targetTabIndex: 3),
          _buildCard("Conexión", txt, Icons.wifi, col, customAction: _intentarReconexion),
        ]),
      ]),
    );
  }
}

// ==========================================
// PESTAÑA 1: MIS REGISTROS
// ==========================================
class TabMisRegistros extends StatefulWidget { const TabMisRegistros({super.key}); @override State<TabMisRegistros> createState() => _TabMisRegistrosState(); }
class _TabMisRegistrosState extends State<TabMisRegistros> {
  List<Registro> _pendientes = []; bool _cargando = false; String? _urlPC;
  @override void initState() { super.initState(); _inicializar(); }
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
  void _editarRegistro(int index, Registro r) { setState(() => _pendientes[index] = r); _guardarDatos(); }
  Future<void> _sincronizar([String? nuevaUrl]) async {
    final prefs = await SharedPreferences.getInstance();
    String? urlUsar = nuevaUrl ?? prefs.getString('pc_ip_url'); // Leer IP fresca
    if (urlUsar == null) return;
    setState(() => _cargando = true);
    final uri = Uri.parse("http://$urlUsar/api/upload");
    List<Registro> enviados = [];
    for (var item in _pendientes) {
      try {
        var req = http.MultipartRequest('POST', uri);
        req.fields['titulo'] = item.titulo;
        req.fields['detalles'] = item.detalles;
        req.fields['tags'] = item.tags;

        // --- AÑADIR ESTO ---
        if (item.fecha != null) req.fields['fecha'] = item.fecha!;
        // -------------------

        if (item.imagePath != null && File(item.imagePath!).existsSync()) {
          req.files.add(await http.MultipartFile.fromPath('foto', item.imagePath!));
        }
        if ((await req.send()).statusCode == 200) enviados.add(item);
      } catch (e) { /* Error */ }
    }
    if (mounted) {
      setState(() { _cargando = false; for (var e in enviados) _pendientes.remove(e); });
      _guardarDatos();
      if (enviados.isNotEmpty) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("✅ ${enviados.length} enviados")));
    }
  }
  @override Widget build(BuildContext context) {
    return Scaffold(
      body: Column(children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), color: Theme.of(context).appBarTheme.backgroundColor?.withOpacity(0.1),
          child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            if (_urlPC != null) TextButton.icon(icon: _cargando ? const SizedBox(width:16,height:16,child:CircularProgressIndicator(strokeWidth:2)) : const Icon(Icons.sync), label: const Text("Sincronizar"), onPressed: () => _sincronizar()),
              IconButton(icon: const Icon(Icons.qr_code), onPressed: () async {
                final ip = await Navigator.push(context, MaterialPageRoute(builder: (_) => const QRScanScreen()));
                if (ip != null) {
                  final prefs = await SharedPreferences.getInstance();
                  await prefs.setString('pc_ip_url', ip);
                  setState(() => _urlPC = ip);
                  _sincronizar(ip);
                }
              })
          ]),
        ),
        Expanded(child: _pendientes.isEmpty ? const Center(child: Text("Sin registros locales", style: TextStyle(color: Colors.grey))) : ListView.builder(itemCount: _pendientes.length, itemBuilder: (ctx, i) {
          final item = _pendientes[i]; File? f = item.imagePath != null ? File(item.imagePath!) : null;
          return Card(child: ListTile(
            leading: f != null && f.existsSync() ? Image.file(f, width: 40, height: 40, fit: BoxFit.cover) : const Icon(Icons.build),
            title: Text(item.titulo, style: const TextStyle(fontWeight: FontWeight.bold)), subtitle: Text(item.detalles, maxLines: 1),
            trailing: IconButton(icon: const Icon(Icons.delete, color: Colors.redAccent), onPressed: () { setState(() => _pendientes.removeAt(i)); _guardarDatos(); }),
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(onSave: (r) => _editarRegistro(i, r), registroExistente: item))),
          ));
        })),
      ]),
      floatingActionButton: FloatingActionButton(child: const Icon(Icons.add), backgroundColor: Colors.blueAccent, onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(onSave: _addRegistro)))),
    );
  }
}

// ==========================================
// PESTAÑA 2: PENDIENTES PC
// ==========================================
class TabPendientesPC extends StatefulWidget { const TabPendientesPC({super.key}); @override State<TabPendientesPC> createState() => _TabPendientesPCState(); }
class _TabPendientesPCState extends State<TabPendientesPC> {
  List<PendientePC> _listaPC = [];
  List<Map<String, dynamic>> _colaSalida = [];
  List<Map<String, dynamic>> _colaNuevos = [];
  List<Map<String, dynamic>> _colaEdiciones = [];
  List<int> _colaBorrados = [];
  Map<String, String> _fotosLocales = {};
  bool _cargando = false; String? _urlPC;

  @override void initState() { super.initState(); _cargarCache(); }
  Future<void> _cargarCache() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _urlPC = prefs.getString('pc_ip_url');
      if (prefs.getString('trabajos_pc') != null) _listaPC = (json.decode(prefs.getString('trabajos_pc')!) as List).map((i) => PendientePC.fromJson(i)).toList();
      if (prefs.getString('cola_salida') != null) _colaSalida = List<Map<String, dynamic>>.from(json.decode(prefs.getString('cola_salida')!));
      if (prefs.getString('cola_nuevos') != null) _colaNuevos = List<Map<String, dynamic>>.from(json.decode(prefs.getString('cola_nuevos')!));
      if (prefs.getString('cola_ediciones') != null) _colaEdiciones = List<Map<String, dynamic>>.from(json.decode(prefs.getString('cola_ediciones')!));
      if (prefs.getString('cola_borrados') != null) _colaBorrados = List<int>.from(json.decode(prefs.getString('cola_borrados')!));
      if (prefs.getString('fotos_locales_map') != null) _fotosLocales = Map<String, String>.from(json.decode(prefs.getString('fotos_locales_map')!));
    });
      _aplicarEdicionesVisuales();
      if (_urlPC != null) _sincronizarTodo(silencioso: true);
  }
  Future<void> _guardarCache() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('trabajos_pc', json.encode(_listaPC.map((p) => {'id': p.id, 'titulo': p.titulo, 'detalles': p.detalles}).toList()));
    await prefs.setString('cola_salida', json.encode(_colaSalida));
    await prefs.setString('cola_nuevos', json.encode(_colaNuevos));
    await prefs.setString('cola_ediciones', json.encode(_colaEdiciones));
    await prefs.setString('cola_borrados', json.encode(_colaBorrados));
    await prefs.setString('fotos_locales_map', json.encode(_fotosLocales));
  }
  void _aplicarEdicionesVisuales() {
    for (var edicion in _colaEdiciones) {
      int index = _listaPC.indexWhere((p) => p.id.toString() == edicion['id']);
      if (index != -1) _listaPC[index] = PendientePC(id: _listaPC[index].id, titulo: edicion['titulo'], detalles: edicion['detalles']);
    }
  }
  Future<String?> _descargarYCachearFoto(String nombreFoto) async {
    try {
      final dir = await getApplicationDocumentsDirectory(); final fp = path.join(dir.path, nombreFoto);
      if (File(fp).existsSync()) return fp;
      if (_urlPC != null) {
        final res = await http.get(Uri.parse("http://$_urlPC/api/foto/$nombreFoto")).timeout(const Duration(seconds: 10));
        if (res.statusCode == 200) { await File(fp).writeAsBytes(res.bodyBytes); return fp; }
      }
    } catch (e) { /* */ } return null;
  }
  Future<void> _sincronizarTodo({bool silencioso = false}) async {
    final prefs = await SharedPreferences.getInstance();
    String? ip = prefs.getString('pc_ip_url'); // Leer IP fresca
    if (ip != null) _urlPC = ip;
    if (_urlPC == null) return;
    if (!silencioso) setState(() => _cargando = true);

    List<int> bo = []; for (var id in _colaBorrados) { if (await _apiPost('eliminar_pendiente', {'id': id.toString()})) bo.add(id); }
    if (bo.isNotEmpty) setState(() { for (var id in bo) _colaBorrados.remove(id); });

    List<Map<String, dynamic>> no = []; for (var t in _colaNuevos) { if (await _apiMultipart('agregar_pendiente', t)) no.add(t); }
    if (no.isNotEmpty) setState(() { for (var t in no) _colaNuevos.remove(t); });

    List<Map<String, dynamic>> eo = []; for (var t in _colaEdiciones) { if (await _apiMultipart('editar_pendiente', t)) eo.add(t); }
    if (eo.isNotEmpty) setState(() { for (var t in eo) _colaEdiciones.remove(t); });

    List<Map<String, dynamic>> so = []; for (var t in _colaSalida) { if (await _apiMultipart('completar_pendiente', t)) so.add(t); }
    if (so.isNotEmpty) setState(() { for (var t in so) _colaSalida.remove(t); });

    await _guardarCache();
    try {
      final res = await http.get(Uri.parse("http://$_urlPC/api/pendientes")).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List<dynamic> d = json.decode(res.body);
        List<PendientePC> nuevos = d.map((i) => PendientePC.fromJson(i)).toList();
        for (var p in nuevos) {
          String? fs = _obtenerFotoServer(p);
          if (fs != null) { String? rl = await _descargarYCachearFoto(fs); if (rl != null) setState(() => _fotosLocales[p.id.toString()] = rl); }
        }
        setState(() => _listaPC = nuevos);
        _aplicarEdicionesVisuales();
        await _guardarCache();
      }
    } catch (e) { /* */ }
    if (!silencioso && mounted) setState(() => _cargando = false);
  }
  Future<bool> _apiPost(String ep, Map<String, String> b) async { try { return (await http.post(Uri.parse("http://$_urlPC/api/$ep"), body: b)).statusCode == 200; } catch (e) { return false; } }
  Future<bool> _apiMultipart(String ep, Map<String, dynamic> d) async {
    try {
      var r = http.MultipartRequest('POST', Uri.parse("http://$_urlPC/api/$ep"));
      if (d.containsKey('id')) r.fields['id'] = d['id'].toString();
      r.fields['titulo'] = d['titulo'];
      r.fields['detalles'] = d['detalles'];
      if (d.containsKey('tags')) r.fields['tags'] = d['tags'];

      // --- AÑADIR ESTO ---
      if (d.containsKey('fecha') && d['fecha'] != null) r.fields['fecha'] = d['fecha'];
      // -------------------

      if (d['imagePath'] != null && File(d['imagePath']).existsSync()) r.files.add(await http.MultipartFile.fromPath('foto', d['imagePath']));
      return (await r.send()).statusCode == 200;
    } catch (e) { return false; }
  }
  String? _obtenerFotoServer(PendientePC p) { final m = RegExp(r"\[FOTO:\s*(.*?)\]").firstMatch(p.detalles); return m?.group(1)?.trim(); }
  String? _obtenerRutaFoto(PendientePC p) {
    String? ref = RegExp(r"\[REF:(\d+)\]").firstMatch(p.detalles)?.group(1);
    if (ref != null && _fotosLocales.containsKey(ref)) return _fotosLocales[ref];
    if (_fotosLocales.containsKey(p.id.toString())) return _fotosLocales[p.id.toString()];
    return null;
  }
  void _abrirGestionar(PendientePC p) async {
    String? fl = _obtenerRutaFoto(p); String? fs = _obtenerFotoServer(p);
    if (fl != null && !File(fl).existsSync()) fl = null;
    Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(
      pendientePC: p, fotoInicialPath: fl, serverImageName: fs, urlPC: _urlPC,
      onSave: (r) {
        String? ref = RegExp(r"\[REF:(\d+)\]").firstMatch(p.detalles)?.group(1);

        // --- AÑADIMOS LA FECHA AL MAPA ---
        Map<String, dynamic> t = {
          'id': p.id,
          'titulo': r.titulo,
          'detalles': r.detalles,
          'tags': r.tags,
          'imagePath': r.imagePath,
          'fecha': r.fecha // <--- NUEVO
        };
        // ---------------------------------

        setState(() {
          _colaSalida.add(t);
          _listaPC.removeWhere((i) => i.id == p.id);
          if (ref != null) _fotosLocales.remove(ref);
          _fotosLocales.remove(p.id.toString());
        });
        _guardarCache();
        _sincronizarTodo(silencioso: true);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Tarea completada")));
      },
      onUpdate: (r) {
        String? ref = RegExp(r"\[REF:(\d+)\]").firstMatch(p.detalles)?.group(1); String k = ref ?? p.id.toString();
        if (r.imagePath != null) setState(() => _fotosLocales[k] = r.imagePath!);
        Map<String, dynamic> t = {'id': p.id, 'titulo': r.titulo, 'detalles': r.detalles, 'tags': r.tags, 'imagePath': r.imagePath};
        setState(() { _colaEdiciones.removeWhere((e) => e['id'] == p.id.toString()); _colaEdiciones.add(t); int i = _listaPC.indexWhere((x) => x.id == p.id); if (i != -1) _listaPC[i] = PendientePC(id: p.id, titulo: r.titulo, detalles: r.detalles); });
        _guardarCache(); _sincronizarTodo(silencioso: true); Navigator.pop(context);
      })));
  }
  @override Widget build(BuildContext context) {
    bool off = _urlPC == null;
    return Scaffold(
      body: Column(children: [
        Expanded(child: _listaPC.isEmpty
        ? RefreshIndicator(onRefresh: _sincronizarTodo, child: ListView(children: [SizedBox(height:MediaQuery.of(context).size.height*0.3), Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [const Icon(Icons.assignment_turned_in, size: 60, color: Colors.grey), const SizedBox(height: 10), const Text("No hay tareas pendientes"), if (off) TextButton.icon(icon: const Icon(Icons.qr_code), label: const Text("Vincular PC"), onPressed: _escanearQR)]))]))
        : RefreshIndicator(onRefresh: _sincronizarTodo, child: ListView.builder(physics: const AlwaysScrollableScrollPhysics(), itemCount: _listaPC.length, itemBuilder: (ctx, i) {
          final item = _listaPC[i]; String? fl = _obtenerRutaFoto(item); String? fs = _obtenerFotoServer(item);
          String limpio = item.detalles.replaceAll(RegExp(r"\[FOTO:.*?\]"), "").replaceAll(RegExp(r"\[REF:.*?\]"), "").trim(); if (limpio.isEmpty) limpio = "Sin detalles";
          Widget ico; if (fl != null) ico = Image.file(File(fl), width: 50, height: 50, fit: BoxFit.cover); else if (fs != null) ico = Container(width:50,height:50,color:Colors.blue.withOpacity(0.1),child:const Icon(Icons.cloud_download,color:Colors.blue)); else ico = CircleAvatar(backgroundColor: Theme.of(context).colorScheme.secondary.withOpacity(0.2), child: Icon(Icons.build, color: Theme.of(context).colorScheme.secondary));
          bool ed = _colaEdiciones.any((e) => e['id'] == item.id.toString());
          return Card(margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), child: ListTile(leading: ClipRRect(borderRadius: BorderRadius.circular(4), child: ico), title: Text(item.titulo, style: const TextStyle(fontWeight: FontWeight.bold)), subtitle: Text(limpio, maxLines: 2, overflow: TextOverflow.ellipsis), onTap: () => _abrirGestionar(item), trailing: ed ? const Icon(Icons.cloud_upload, color: Colors.orange) : IconButton(icon: const Icon(Icons.delete, color: Colors.grey), onPressed: () => _borrar(item.id))));
        }))),
      ]),
      floatingActionButton: FloatingActionButton.extended(backgroundColor: Theme.of(context).colorScheme.secondary, foregroundColor: Colors.white, icon: const Icon(Icons.add_task), label: const Text("AÑADIR"), onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(esCrearPendiente: true, onSave: (r) {
        String ru = DateTime.now().millisecondsSinceEpoch.toString(); if (r.imagePath != null) setState(() => _fotosLocales[ru] = r.imagePath!);
        String d = "${r.detalles} [REF:$ru]"; Map<String, dynamic> t = {'titulo': r.titulo, 'detalles': d, 'tags': r.tags, 'imagePath': r.imagePath};
        setState(() => _colaNuevos.add(t)); setState(() => _listaPC.insert(0, PendientePC(id: -DateTime.now().millisecondsSinceEpoch, titulo: r.titulo, detalles: d)));
        _guardarCache(); _sincronizarTodo(silencioso: true); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Pendiente creado")));
      })))),
    );
  }
  void _borrar(int id) async { if (await showDialog(context: context, builder: (ctx) => AlertDialog(title: const Text("¿Borrar?"), actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("NO")), TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("SÍ", style: TextStyle(color: Colors.red)))])) == true) { setState(() { _listaPC.removeWhere((p) => p.id == id); _colaBorrados.add(id); }); _guardarCache(); _sincronizarTodo(silencioso: true); } }
  Future<void> _escanearQR() async { final c = await Navigator.push(context, MaterialPageRoute(builder: (_) => const QRScanScreen())); if (c != null) { final prefs = await SharedPreferences.getInstance(); await prefs.setString('pc_ip_url', c); setState(() => _urlPC = c); _sincronizarTodo(); } }
}

// ==========================================
// PESTAÑA 3: AVISOS
// ==========================================
class TabAvisos extends StatefulWidget { const TabAvisos({super.key}); @override State<TabAvisos> createState() => _TabAvisosState(); }
class _TabAvisosState extends State<TabAvisos> {
  List<AvisoPC> _avisos = [];
  List<Map<String, String>> _colaCompletados = [];
  List<String> _colaRestaurar = [];
  bool _cargando = false; String? _urlPC;

  @override void initState() { super.initState(); _inicializar(); }
  Future<void> _inicializar() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() => _urlPC = prefs.getString('pc_ip_url'));

    // CORRECCIÓN CRÍTICA DE TIPOS
    String? cc = prefs.getString('avisos_cola_completados');
    if (cc != null) {
      List<dynamic> dec = json.decode(cc);
      _colaCompletados = dec.map((e) => Map<String, String>.from(e)).toList();
    }

    String? cr = prefs.getString('avisos_cola_restaurar');
    if (cr != null) _colaRestaurar = List<String>.from(json.decode(cr));

    if (prefs.getString('avisos_cache') != null) {
      try {
        final List<dynamic> d = json.decode(prefs.getString('avisos_cache')!);
        setState(() => _avisos = d.map((x) => AvisoPC.fromJson(x)).toList());
      } catch (e) { /* */ }
    }
    if (_urlPC != null) _sincronizar();
  }
  Future<void> _guardarColas() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('avisos_cola_completados', json.encode(_colaCompletados));
    await prefs.setString('avisos_cola_restaurar', json.encode(_colaRestaurar));
  }
  Future<void> _sincronizar() async {
    final prefs = await SharedPreferences.getInstance();
    String? ip = prefs.getString('pc_ip_url'); // Leer IP fresca
    if (ip != null) _urlPC = ip;
    if (_urlPC == null) return;
    if (!mounted) return;
    setState(() => _cargando = true);

    List<String> ro = []; for (var id in _colaRestaurar) { try { if ((await http.post(Uri.parse("http://$_urlPC/api/descompletar_aviso"), body: {'id': id}).timeout(const Duration(seconds: 5))).statusCode == 200) ro.add(id); } catch (e) { /* */ } }
    List<Map<String, String>> co = []; for (var item in _colaCompletados) { try { if ((await http.post(Uri.parse("http://$_urlPC/api/completar_aviso"), body: {'id': item['id'], 'titulo': item['titulo'], 'fecha_custom': item['fecha']}).timeout(const Duration(seconds: 5))).statusCode == 200) co.add(item); } catch (e) { /* */ } }

    if (ro.isNotEmpty || co.isNotEmpty) { setState(() { for (var id in ro) _colaRestaurar.remove(id); for (var item in co) _colaCompletados.remove(item); }); await _guardarColas(); }
    try {
      final res = await http.get(Uri.parse("http://$_urlPC/api/avisos")).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List<dynamic> d = json.decode(res.body);
        setState(() => _avisos = d.map((x) => AvisoPC.fromJson(x)).toList());
        await prefs.setString('avisos_cache', res.body);
      }
    } catch (e) { /* */ } finally { if (mounted) setState(() => _cargando = false); }
  }
  Future<void> _completar(AvisoPC a) async {
    if (_colaRestaurar.contains(a.id.toString())) { setState(() => _colaRestaurar.remove(a.id.toString())); await _guardarColas(); return; }
    if (await showDialog(context: context, builder: (ctx) => AlertDialog(title: const Text("Confirmar"), content: Text("¿Marcar '${a.titulo}'?"), actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("NO")), ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.green), onPressed: () => Navigator.pop(ctx, true), child: const Text("SÍ", style: TextStyle(color: Colors.white)))])) != true) return;
    setState(() => _colaCompletados.add({'id': a.id.toString(), 'titulo': a.titulo, 'fecha': DateTime.now().toString().split(' ')[0]})); await _guardarColas(); _sincronizar();
  }
  Future<void> _descompletar(AvisoPC a) async {
    if (_colaCompletados.any((i) => i['id'] == a.id.toString())) { setState(() => _colaCompletados.removeWhere((i) => i['id'] == a.id.toString())); await _guardarColas(); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("↩️ Deshecho"))); return; }
    if (await showDialog(context: context, builder: (ctx) => AlertDialog(title: const Text("Desmarcar"), content: const Text("¿Volver a pendiente?"), actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("CANCELAR")), ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.red), onPressed: () => Navigator.pop(ctx, true), child: const Text("DESMARCAR", style: TextStyle(color: Colors.white)))])) != true) return;
    setState(() => _colaRestaurar.add(a.id.toString())); await _guardarColas(); _sincronizar();
  }
  @override Widget build(BuildContext context) {
    if (_urlPC == null && _avisos.isEmpty) return const Center(child: Text("Conecta el PC para sincronizar"));
    int p = _colaCompletados.length + _colaRestaurar.length;
    return Scaffold(
      body: Column(children: [
        if (p > 0) Container(width: double.infinity, color: Colors.orangeAccent, padding: const EdgeInsets.all(8), child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [const Icon(Icons.cloud_upload, color: Colors.white, size: 16), const SizedBox(width: 8), Text("$p cambios pendientes", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold))])),
          Expanded(child: _avisos.isEmpty
          ? RefreshIndicator(onRefresh: _sincronizar, child: ListView(children:[SizedBox(height:MediaQuery.of(context).size.height*0.3), const Center(child:Text("No hay avisos"))]))
          : RefreshIndicator(onRefresh: _sincronizar, child: ListView.builder(physics: const AlwaysScrollableScrollPhysics(), padding: const EdgeInsets.all(10), itemCount: _avisos.length, itemBuilder: (ctx, i) {
            final a = _avisos[i]; String id = a.id.toString(); bool ec = _colaCompletados.any((x) => x['id'] == id); bool er = _colaRestaurar.contains(id);
            String st = a.estado; String cl = a.color; if (ec) { st = "LISTO (Subir)"; cl = "green"; } else if (er) { st = "PENDIENTE (Subir)"; cl = "red"; }
            Color c = cl == 'red' ? Colors.redAccent : (cl == 'green' ? Colors.green : Colors.blue);
            Widget w; if (cl == 'green') { w = ActionChip(avatar: ec ? const Icon(Icons.undo,size:14,color:Colors.white):const Icon(Icons.close,size:14,color:Colors.white), label: Text(ec?"Deshacer":"Desmarcar",style:const TextStyle(color:Colors.white,fontSize:10)), backgroundColor: c, onPressed: () => _descompletar(a)); } else if (cl == 'red') { w = ElevatedButton.icon(style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5), visualDensity: VisualDensity.compact), icon: const Icon(Icons.check, size: 16), label: const Text("Completar"), onPressed: () => _completar(a)); } else { w = Chip(label: Text(st, style: const TextStyle(color: Colors.white, fontSize: 10)), backgroundColor: c); }
            return Card(elevation: 2, margin: const EdgeInsets.symmetric(vertical: 6), shape: RoundedRectangleBorder(side: BorderSide(color: c.withOpacity(0.3)), borderRadius: BorderRadius.circular(8)), child: ListTile(leading: Container(padding: const EdgeInsets.all(8), decoration: BoxDecoration(color: c.withOpacity(0.1), shape: BoxShape.circle), child: Icon(cl=='red'?Icons.warning_amber_rounded:(cl=='green'?Icons.check_circle_outline:Icons.calendar_month), color: c, size: 24)), title: Text(a.titulo, style: const TextStyle(fontWeight: FontWeight.bold)), subtitle: Text("Próxima: ${a.rango}", style: const TextStyle(fontSize: 12)), trailing: w));
          }))),
      ]),
      floatingActionButton: FloatingActionButton(mini: true, backgroundColor: p>0?Colors.white:Colors.blue, child: _cargando ? const Padding(padding:EdgeInsets.all(10),child:CircularProgressIndicator(color:Colors.white,strokeWidth:2)) : Icon(Icons.sync, color: p>0?Colors.orange:Colors.white), onPressed: _sincronizar),
    );
  }
}

// ==========================================
// PESTAÑA 4: HISTORIAL
// ==========================================
class TabHistorial extends StatefulWidget { const TabHistorial({super.key}); @override State<TabHistorial> createState() => _TabHistorialState(); }
class _TabHistorialState extends State<TabHistorial> {
  List<Registro> _registros = []; List<Map<String, dynamic>> _colaEdiciones = [];
  bool _cargando = false; String? _urlPC; final _searchCtrl = TextEditingController();
  @override void initState() { super.initState(); _inicializarHistorial(); }
  Future<void> _inicializarHistorial() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() => _urlPC = prefs.getString('pc_ip_url'));
    if (prefs.getString('historial_cola_ediciones') != null) _colaEdiciones = List<Map<String, dynamic>>.from(json.decode(prefs.getString('historial_cola_ediciones')!));
    if (prefs.getString('historial_cache') != null) { try { final List<dynamic> d = json.decode(prefs.getString('historial_cache')!); setState(() => _registros = d.map((i) => Registro.fromJson(i)).toList()); _aplicarCambiosVisuales(); } catch (e) { /* */ } }
    if (_urlPC != null) { _sincronizarCompleto(); }
  }
  Future<void> _sincronizarCompleto() async {
    final prefs = await SharedPreferences.getInstance(); String? ip = prefs.getString('pc_ip_url'); if (ip != null) _urlPC = ip;
    if (_urlPC == null) return;
    await _sincronizarEdiciones(); await _buscar("");
  }
  Future<void> _guardarCola() async { final p = await SharedPreferences.getInstance(); await p.setString('historial_cola_ediciones', json.encode(_colaEdiciones)); }
  void _aplicarCambiosVisuales() {
    for (var e in _colaEdiciones) { int i = _registros.indexWhere((r) => r.id.toString() == e['id']); if (i != -1) _registros[i] = Registro(id: _registros[i].id, titulo: _registros[i].titulo, detalles: e['detalles'], tags: e['tags'], serverImageName: _registros[i].serverImageName, imagePath: e['fotoPath'] ?? _registros[i].imagePath); }
  }
  Future<void> _sincronizarEdiciones() async {
    if (_urlPC == null || _colaEdiciones.isEmpty) return;
    List<Map<String, dynamic>> ok = [];
    for (var e in _colaEdiciones) {
      try {
        var req = http.MultipartRequest('POST', Uri.parse("http://$_urlPC/api/editar_historial"));
        req.fields['id'] = e['id']; req.fields['detalles'] = e['detalles']; req.fields['tags'] = e['tags'];
        if (e['fotoPath'] != null && File(e['fotoPath']).existsSync()) req.files.add(await http.MultipartFile.fromPath('foto', e['fotoPath']));
        if ((await req.send()).statusCode == 200) ok.add(e);
      } catch (e) { /* */ }
    }
    if (ok.isNotEmpty) { setState(() { for (var s in ok) _colaEdiciones.remove(s); }); await _guardarCola(); }
  }
  Future<void> _buscar(String q) async {
    final prefs = await SharedPreferences.getInstance(); String? ip = prefs.getString('pc_ip_url'); if (ip != null) _urlPC = ip;
    if (_urlPC == null) return;
    setState(() => _cargando = true);
    try {
      final res = await http.get(Uri.parse("http://$_urlPC/api/historial?q=$q")).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List<dynamic> d = json.decode(res.body);
        List<Registro> news = d.map((i) => Registro(id: i['id'], titulo: "${i['fecha']}", detalles: i['descripcion'], tags: i['tags'], serverImageName: i['foto'], imagePath: i['raw_desc'])).toList();
        final dir = await getApplicationDocumentsDirectory();
        for (var r in news) {
          if (r.serverImageName != null) { final fp = path.join(dir.path, r.serverImageName!); if (!File(fp).existsSync()) { try { var ir = await http.get(Uri.parse("http://$_urlPC/api/foto/${r.serverImageName}")); if (ir.statusCode == 200) await File(fp).writeAsBytes(ir.bodyBytes); } catch (e) { /* */ } } }
        }
        setState(() => _registros = news); _aplicarCambiosVisuales(); await prefs.setString('historial_cache', json.encode(news.map((r) => r.toJson()).toList()));
      }
    } catch (e) { /* */ } finally { if (mounted) setState(() => _cargando = false); }
  }
  Future<String> _localPath(String f) async { final d = await getApplicationDocumentsDirectory(); return path.join(d.path, f); }
  void _edit(Registro r) async {
    String? lp; var ep = _colaEdiciones.firstWhere((e) => e['id'] == r.id.toString(), orElse: () => {});
    if (ep.isNotEmpty && ep['fotoPath'] != null) lp = ep['fotoPath']; else if (r.serverImageName != null) { final fp = await _localPath(r.serverImageName!); if (File(fp).existsSync()) lp = fp; }
    await Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(registroExistente: Registro(id: r.id, titulo: "", detalles: r.imagePath??r.detalles, tags: r.tags, imagePath: lp), esHistorial: true, onSave: (re) async {
      Map<String, dynamic> ne = {'id': r.id.toString(), 'detalles': re.detalles, 'tags': re.tags, 'fotoPath': re.imagePath};
      int i = _colaEdiciones.indexWhere((e) => e['id'] == r.id.toString()); if (i != -1) _colaEdiciones[i] = ne; else _colaEdiciones.add(ne);
      await _guardarCola(); setState(() => _aplicarCambiosVisuales()); _sincronizarEdiciones(); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Guardado")));
    })));
  }
  @override Widget build(BuildContext context) {
    return Scaffold(
      body: Column(children: [
        if (_colaEdiciones.isNotEmpty) Container(width: double.infinity, color: Colors.orangeAccent, padding: const EdgeInsets.all(8), child: Text("${_colaEdiciones.length} pendientes de subir", textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold))),
          Padding(padding: const EdgeInsets.all(8.0), child: TextField(controller: _searchCtrl, decoration: InputDecoration(hintText: "Buscar historial...", suffixIcon: IconButton(icon: const Icon(Icons.search), onPressed: () => _buscar(_searchCtrl.text)), border: const OutlineInputBorder(), filled: _urlPC == null, fillColor: _urlPC == null ? Colors.red.withOpacity(0.05) : null), onSubmitted: _buscar)),
          Expanded(child: RefreshIndicator(onRefresh: _sincronizarCompleto, child: _registros.isEmpty
          ? ListView(children:[SizedBox(height:MediaQuery.of(context).size.height*0.3), const Center(child:Text("Sin historial visible"))])
          : ListView.builder(itemCount: _registros.length, itemBuilder: (ctx, i) {
            final r = _registros[i]; Widget w;
            if (r.imagePath != null && File(r.imagePath!).existsSync() && !r.imagePath!.contains("[")) w = Image.file(File(r.imagePath!), width: 50, height: 50, fit: BoxFit.cover);
            else if (r.serverImageName != null) w = FutureBuilder<String>(future: _localPath(r.serverImageName!), builder: (c, s) { if (s.hasData && File(s.data!).existsSync()) return Image.file(File(s.data!), width: 50, height: 50, fit: BoxFit.cover); else if (_urlPC != null) return Image.network("http://$_urlPC/api/foto/${r.serverImageName}", width: 50, height: 50, fit: BoxFit.cover, errorBuilder: (c, e, s) => const Icon(Icons.broken_image, color: Colors.red)); else return const Icon(Icons.no_photography, color: Colors.grey); });
              else w = const Icon(Icons.article, color: Colors.blueGrey);
              bool p = _colaEdiciones.any((e) => e['id'] == r.id.toString());
            return Card(color: p ? Colors.orange.withOpacity(0.1) : null, margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), child: ListTile(leading: ClipRRect(borderRadius: BorderRadius.circular(4), child: SizedBox(width: 50, height: 50, child: Center(child: w))), title: Text(r.detalles, maxLines: 2, overflow: TextOverflow.ellipsis), subtitle: Text("${r.titulo} | ${r.tags}"), trailing: Icon(p ? Icons.cloud_upload : Icons.edit, size: 20, color: p ? Colors.orange : Colors.blueGrey), onTap: () => _edit(r)));
          })))
      ]),
      floatingActionButton: FloatingActionButton(mini: true, backgroundColor: Colors.blue, child: _cargando ? const Padding(padding:EdgeInsets.all(10),child:CircularProgressIndicator(color:Colors.white,strokeWidth:2)) : const Icon(Icons.sync, color: Colors.white), onPressed: _sincronizarCompleto),
    );
  }
}

// ==========================================
// FORMULARIO Y QR (COMPACTOS)
// ==========================================
class FormScreen extends StatefulWidget { final Function(Registro) onSave; final Function(Registro)? onUpdate; final PendientePC? pendientePC; final Registro? registroExistente; final bool esCrearPendiente, esHistorial; final String? fotoInicialPath, serverImageName, urlPC; const FormScreen({super.key, required this.onSave, this.onUpdate, this.pendientePC, this.registroExistente, this.esCrearPendiente=false, this.esHistorial=false, this.fotoInicialPath, this.serverImageName, this.urlPC}); @override State<FormScreen> createState() => _FormScreenState(); }
class _FormScreenState extends State<FormScreen> {
  final _t = TextEditingController(); final _d = TextEditingController(); final _tag = TextEditingController(); String? _img;
  bool _u=false, _e=false, _m=false, _p=false;
  @override void initState() { super.initState();
    if (widget.pendientePC != null) { _t.text = widget.pendientePC!.titulo; _d.text = widget.pendientePC!.detalles.replaceAll(RegExp(r"\[FOTO:.*?\]"), "").replaceAll(RegExp(r"\[REF:.*?\]"), "").trim(); if (widget.fotoInicialPath != null) _img = widget.fotoInicialPath; }
    if (widget.registroExistente != null) { final r = widget.registroExistente!; if (r.titulo.isNotEmpty) _t.text = r.titulo; _d.text = r.detalles.replaceAll(RegExp(r"\[FOTO:.*?\]"), "").replaceAll(RegExp(r"\[REF:.*?\]"), "").trim(); if (r.imagePath != null && File(r.imagePath!).existsSync()) _img = r.imagePath; _u=r.tags.contains("Urgente"); _e=r.tags.contains("Eléctrico"); _m=r.tags.contains("Mecánico"); _p=r.tags.contains("Preventivo"); _tag.text = r.tags.split(', ').where((t) => !['Urgente','Eléctrico','Mecánico','Preventivo'].contains(t)).join(', '); }
  }
  void _save(bool end) {
    if (_t.text.isEmpty && !widget.esHistorial) return;

    List<String> l=[];
    if(_u)l.add("Urgente"); if(_e)l.add("Eléctrico"); if(_m)l.add("Mecánico"); if(_p)l.add("Preventivo");
    if(_tag.text.isNotEmpty)l.add(_tag.text.trim());

    String df = _d.text;
    if (widget.pendientePC != null) {
      final m = RegExp(r"\[REF:(\d+)\]").firstMatch(widget.pendientePC!.detalles);
      if (m != null) df += " ${m.group(0)}";
    }

    // --- CAMBIO AQUÍ: GUARDAR FECHA SI TERMINAMOS ---
    String? fechaFinal;
    if (widget.registroExistente?.fecha != null) {
      fechaFinal = widget.registroExistente!.fecha; // Mantener original si ya existía
    }
    if (end) {
      // Si terminamos ahora, guardamos YYYY-MM-DD
      fechaFinal = DateTime.now().toString().substring(0, 10);
    }
    // -----------------------------------------------

    Registro r = Registro(
      id: widget.registroExistente?.id,
      titulo: _t.text,
      detalles: df,
      tags: l.join(", "),
      imagePath: _img,
      fecha: fechaFinal // <--- PASAR LA FECHA
    );

    if (end) widget.onSave(r); else if (widget.onUpdate != null) widget.onUpdate!(r); else widget.onSave(r);
    if (widget.onUpdate == null || end) Navigator.pop(context);
  }
  Future<void> _cam() async { final f = await ImagePicker().pickImage(source: ImageSource.camera, imageQuality: 60); if (f!=null) { final d = await getApplicationDocumentsDirectory(); final n = path.join(d.path, 'foto_${DateTime.now().millisecondsSinceEpoch}.jpg'); await File(f.path).copy(n); setState(() => _img = n); } }
  Future<void> _down() async { if (widget.serverImageName!=null && widget.urlPC!=null) { final d = await getApplicationDocumentsDirectory(); final fp = path.join(d.path, widget.serverImageName!); var r = await http.get(Uri.parse("http://${widget.urlPC}/api/foto/${widget.serverImageName}")); if (r.statusCode==200) { await File(fp).writeAsBytes(r.bodyBytes); setState(() => _img = fp); } } }
  @override Widget build(BuildContext context) {
    return Scaffold(appBar: AppBar(title: Text(widget.esHistorial?"Editar": "Nuevo")), body: SingleChildScrollView(padding: const EdgeInsets.all(16), child: Column(children: [
      if(!widget.esHistorial) TextField(controller: _t, decoration: const InputDecoration(labelText: "Título")), const SizedBox(height: 15),
        TextField(controller: _d, maxLines: 5, decoration: const InputDecoration(labelText: "Detalles")), const SizedBox(height: 15),
        Wrap(spacing: 8, children: [FilterChip(label: const Text('🚨 Urgente'), selected: _u, onSelected: (v)=>setState(()=>_u=v)), FilterChip(label: const Text('⚡ Eléctrico'), selected: _e, onSelected: (v)=>setState(()=>_e=v)), FilterChip(label: const Text('⚙️ Mecánico'), selected: _m, onSelected: (v)=>setState(()=>_m=v)), FilterChip(label: const Text('🛡️ Preventivo'), selected: _p, onSelected: (v)=>setState(()=>_p=v))]),
        TextField(controller: _tag, decoration: const InputDecoration(labelText: "Tags extra")), const SizedBox(height: 15), const Divider(),
        if (_img != null) ...[SizedBox(height: 300, child: Image.file(File(_img!))), ElevatedButton.icon(icon: const Icon(Icons.delete), label: const Text("BORRAR"), style: ElevatedButton.styleFrom(backgroundColor: Colors.red), onPressed: () => setState(() => _img = null))]
          else ...[if (widget.serverImageName!=null) ElevatedButton.icon(icon: const Icon(Icons.cloud_download), label: const Text("DESCARGAR FOTO"), onPressed: _down), ElevatedButton.icon(icon: const Icon(Icons.camera_alt), label: const Text("FOTO"), onPressed: _cam)],
            const SizedBox(height: 20),
            if (widget.pendientePC != null) Row(children: [Expanded(child: ElevatedButton(onPressed: ()=>_save(false), child: const Text("ACTUALIZAR"))), const SizedBox(width: 10), Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.green), onPressed: ()=>_save(true), child: const Text("TERMINAR")))])
              else ElevatedButton(style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(50)), onPressed: ()=>_save(true), child: const Text("GUARDAR"))
    ])));
  }
}
class QRScanScreen extends StatefulWidget { const QRScanScreen({super.key}); @override State<QRScanScreen> createState() => _QRScanScreenState(); }
class _QRScanScreenState extends State<QRScanScreen> {
  bool _s = false;
  @override Widget build(BuildContext context) { return Scaffold(appBar: AppBar(title: const Text("QR")), body: MobileScanner(onDetect: (c) { if (!_s && c.barcodes.isNotEmpty && c.barcodes.first.rawValue!=null) { setState(()=>_s=true); Navigator.pop(context, c.barcodes.first.rawValue!.replaceAll("http://", "").replaceAll("/", "")); } })); }
}
class ImageEditorScreen extends StatefulWidget { final File imageFile; const ImageEditorScreen({super.key, required this.imageFile}); @override State<ImageEditorScreen> createState() => _ImageEditorScreenState(); }
class _ImageEditorScreenState extends State<ImageEditorScreen> {
  final _c = ImagePainterController(color: Colors.red, strokeWidth: 4.0, mode: PaintMode.freeStyle); bool _g = false;
  @override void initState() { super.initState(); SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]); }
  @override void dispose() { SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp, DeviceOrientation.portraitDown, DeviceOrientation.landscapeLeft, DeviceOrientation.landscapeRight]); super.dispose(); }
  @override Widget build(BuildContext context) { return WillPopScope(onWillPop: () async => !_g, child: Scaffold(backgroundColor: Colors.black, appBar: AppBar(actions: [IconButton(icon: const Icon(Icons.check), onPressed: () async { setState(()=>_g=true); final b = await _c.exportImage(); if (b!=null) { await widget.imageFile.writeAsBytes(b); if (mounted) Navigator.pop(context, true); } setState(()=>_g=false); })]), body: ImagePainter.file(widget.imageFile, controller: _c, scalable: true))); }
}
