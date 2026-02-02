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
// Usamos un Notifier global para poder acceder desde cualquier sitio
final ValueNotifier<ThemeMode> themeNotifier = ValueNotifier(ThemeMode.dark);

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Cargar preferencia de tema guardada
  final prefs = await SharedPreferences.getInstance();
  final bool isDark = prefs.getBool('is_dark_mode') ?? true; // Por defecto oscuro
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

          // --- TEMA CLARO ---
          theme: ThemeData.light().copyWith(
            scaffoldBackgroundColor: Colors.grey[100],
            appBarTheme: const AppBarTheme(
              backgroundColor: Colors.blueGrey,
              foregroundColor: Colors.white,
            ),
            cardColor: Colors.white,
            bottomNavigationBarTheme: const BottomNavigationBarThemeData(
              backgroundColor: Colors.blueGrey,
              selectedItemColor: Colors.white,
              unselectedItemColor: Colors.white60,
            ),
          ),

          // --- TEMA OSCURO (El que te gusta) ---
          darkTheme: ThemeData.dark().copyWith(
            scaffoldBackgroundColor: Colors.grey[900],
            appBarTheme: AppBarTheme(backgroundColor: Colors.grey[850]),
            cardColor: Colors.grey[800],
            bottomNavigationBarTheme: BottomNavigationBarThemeData(
              backgroundColor: Colors.grey[850],
              selectedItemColor: Colors.white,
              unselectedItemColor: Colors.white54,
            ),
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
  String titulo, detalles, tags;
  String? imagePath;
  Registro(
    {required this.titulo,
      required this.detalles,
      required this.tags,
      this.imagePath});

  Map<String, dynamic> toJson() => {
    'titulo': titulo,
    'detalles': detalles,
    'tags': tags,
    'imagePath': imagePath
  };

  factory Registro.fromJson(Map<String, dynamic> json) => Registro(
    titulo: json['titulo'],
    detalles: json['detalles'],
    tags: json['tags'],
    imagePath: json['imagePath']);
}

class PendientePC {
  int id;
  String titulo, detalles;
  PendientePC({required this.id, required this.titulo, required this.detalles});
  factory PendientePC.fromJson(Map<String, dynamic> json) => PendientePC(
    id: json['id'], titulo: json['titulo'], detalles: json['detalles']);
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
  final List<Widget> _pantallas = [
    const TabMisRegistros(),
    const TabPendientesPC()
  ];

  // Función para alternar tema
  void _toggleTheme() async {
    final prefs = await SharedPreferences.getInstance();
    if (themeNotifier.value == ThemeMode.dark) {
      themeNotifier.value = ThemeMode.light;
      await prefs.setBool('is_dark_mode', false);
    } else {
      themeNotifier.value = ThemeMode.dark;
      await prefs.setBool('is_dark_mode', true);
    }
  }

  @override
  Widget build(BuildContext context) {
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      // AppBar Común para tener el botón de tema siempre visible
      appBar: AppBar(
        title: Text(_indiceActual == 0 ? "Mis Registros" : "Trabajos Pendientes"),
        actions: [
          // BOTÓN DE TEMA (SOL/LUNA)
          IconButton(
            icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode),
            tooltip: "Cambiar Tema",
            onPressed: _toggleTheme,
          ),
        ],
      ),
      body: IndexedStack(index: _indiceActual, children: _pantallas),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _indiceActual,
        onTap: (index) => setState(() => _indiceActual = index),
        // Los colores ahora se cogen del Theme definido en MyApp
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.folder), label: "Mis Registros"),
            BottomNavigationBarItem(
              icon: Icon(Icons.list_alt), label: "Trabajos Pendientes"),
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
      setState(() =>
      _pendientes = l.map((item) => Registro.fromJson(item)).toList());
    }
    setState(() => _urlPC = prefs.getString('pc_ip_url'));
    if (_pendientes.isNotEmpty && _urlPC != null) _sincronizar();
  }

  Future<void> _guardarDatos() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('registros_pendientes',
                          json.encode(_pendientes.map((r) => r.toJson()).toList()));
  }

  void _addRegistro(Registro r) {
    setState(() => _pendientes.add(r));
    _guardarDatos();
  }

  void _borrarRegistro(int i) {
    setState(() => _pendientes.removeAt(i));
    _guardarDatos();
  }

  void _editarRegistro(int index, Registro r) {
    setState(() => _pendientes[index] = r);
    _guardarDatos();
  }

  Future<void> _confirmarBorrado(int index) async {
    final bool? confirmar = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("¿Borrar?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text("CANCELAR")),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text("BORRAR", style: TextStyle(color: Colors.red))),
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
    final uri = Uri.parse("http://$urlUsar/api/upload");
    List<Registro> enviados = [];

    for (var item in _pendientes) {
      try {
        var req = http.MultipartRequest('POST', uri);
        req.fields['titulo'] = item.titulo;
        req.fields['detalles'] = item.detalles;
        req.fields['tags'] = item.tags;
        if (item.imagePath != null && File(item.imagePath!).existsSync()) {
          req.files
          .add(await http.MultipartFile.fromPath('foto', item.imagePath!));
        }
        var res = await req.send();
        if (res.statusCode == 200) enviados.add(item);
      } catch (e) {
        /* Error */
      }
    }

    if (mounted) {
      setState(() => _cargando = false);
      if (enviados.isNotEmpty) {
        setState(() {
          for (var e in enviados) _pendientes.remove(e);
        });
          _guardarDatos();
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("✅ ${enviados.length} enviados")));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // IMPORTANTE: Quitamos el AppBar de aquí porque ahora está en MainScreen
    return Scaffold(
      body: Column(
        children: [
          // Barra de herramientas superior personalizada para esta pestaña
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            color: Theme.of(context).appBarTheme.backgroundColor?.withOpacity(0.1),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                if (_urlPC != null)
                  TextButton.icon(
                    icon: _cargando
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.sync),
                    label: const Text("Sincronizar"),
                    onPressed: () => _sincronizar(),
                  ),
                  IconButton(
                    icon: const Icon(Icons.qr_code),
                    tooltip: "Cambiar PC",
                    onPressed: () async {
                      final ip = await Navigator.push(context,
                                                      MaterialPageRoute(builder: (_) => const QRScanScreen()));
                      if (ip != null) _sincronizar(ip);
                    }),
              ],
            ),
          ),
          Expanded(
            child: _pendientes.isEmpty
            ? const Center(
              child: Text("Sin registros locales",
                          style: TextStyle(color: Colors.grey)))
            : ListView.builder(
              itemCount: _pendientes.length,
              itemBuilder: (ctx, i) {
                final item = _pendientes[i];
                File? f =
                item.imagePath != null ? File(item.imagePath!) : null;
                return Card(
                  // Eliminamos color hardcoded para usar el del tema
                  child: ListTile(
                    leading: f != null && f.existsSync()
                    ? Image.file(f,
                                 width: 40, height: 40, fit: BoxFit.cover)
                    : const Icon(Icons.build),
                    title: Text(item.titulo,
                                style: const TextStyle(fontWeight: FontWeight.bold)),
                                subtitle: Text(item.detalles, maxLines: 1),
                                trailing: IconButton(
                                  icon: const Icon(Icons.delete, color: Colors.redAccent),
                                  onPressed: () => _confirmarBorrado(i)),
                                  onTap: () => Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => FormScreen(
                                        onSave: (r) => _editarRegistro(i, r),
                                        registroExistente: item))),
                  ),
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        child: const Icon(Icons.add),
        backgroundColor: Colors.blueAccent,
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => FormScreen(onSave: _addRegistro)))),
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
      if (l != null) {
        _listaPC = (json.decode(l) as List)
        .map((i) => PendientePC.fromJson(i))
        .toList();
      }

      String? c = prefs.getString('cola_salida');
      if (c != null) {
        _colaSalida = List<Map<String, dynamic>>.from(json.decode(c));
      }

      String? n = prefs.getString('cola_nuevos');
      if (n != null) {
        _colaNuevos = List<Map<String, dynamic>>.from(json.decode(n));
      }

      String? e = prefs.getString('cola_edicion');
      if (e != null) {
        _colaEdicion = List<Map<String, dynamic>>.from(json.decode(e));
      }

      String? b = prefs.getString('cola_borrados');
      if (b != null) _colaBorrados = List<int>.from(json.decode(b));

      String? f = prefs.getString('fotos_locales_map');
      if (f != null) _fotosLocales = Map<String, String>.from(json.decode(f));
    });

      if (_urlPC != null) _sincronizarTodo(silencioso: true);
  }

  Future<void> _guardarCache() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      'trabajos_pc',
      json.encode(_listaPC
      .map((p) =>
      {'id': p.id, 'titulo': p.titulo, 'detalles': p.detalles})
      .toList()));
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
    for (var id in _colaBorrados) {
      if (await _apiPost('eliminar_pendiente', {'id': id.toString()})) {
        borradosOk.add(id);
      }
    }
    if (borradosOk.isNotEmpty) {
      setState(() {
        for (var id in borradosOk) _colaBorrados.remove(id);
      });
    }

    List<Map<String, dynamic>> nuevosOk = [];
    for (var t in _colaNuevos) {
      if (await _apiMultipart('agregar_pendiente', t)) nuevosOk.add(t);
    }
    if (nuevosOk.isNotEmpty) {
      setState(() {
        for (var t in nuevosOk) _colaNuevos.remove(t);
      });
    }

    List<Map<String, dynamic>> edicionOk = [];
    for (var t in _colaEdicion) {
      if (await _apiMultipart('editar_pendiente', t)) edicionOk.add(t);
    }
    if (edicionOk.isNotEmpty) {
      setState(() {
        for (var t in edicionOk) _colaEdicion.remove(t);
      });
    }

    List<Map<String, dynamic>> salidaOk = [];
    for (var t in _colaSalida) {
      if (await _apiMultipart('completar_pendiente', t)) salidaOk.add(t);
    }
    if (salidaOk.isNotEmpty) {
      setState(() {
        for (var t in salidaOk) _colaSalida.remove(t);
      });
    }

    await _guardarCache();

    try {
      final res = await http
      .get(Uri.parse("http://$_urlPC/api/pendientes"))
      .timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List<dynamic> datos = json.decode(res.body);
        setState(() => _listaPC =
        datos.map((item) => PendientePC.fromJson(item)).toList());
        await _guardarCache();
      }
    } catch (e) {
      // Error de red
    }

    if (!silencioso && mounted) setState(() => _cargando = false);
  }

  Future<bool> _apiPost(String endpoint, Map<String, String> body) async {
    try {
      return (await http.post(Uri.parse("http://$_urlPC/api/$endpoint"),
      body: body))
      .statusCode ==
      200;
    } catch (e) {
      return false;
    }
  }

  Future<bool> _apiMultipart(
    String endpoint, Map<String, dynamic> datos) async {
      try {
        var req = http.MultipartRequest(
          'POST', Uri.parse("http://$_urlPC/api/$endpoint"));
        if (datos.containsKey('id')) req.fields['id'] = datos['id'].toString();
        req.fields['titulo'] = datos['titulo'];
        req.fields['detalles'] = datos['detalles'];
        if (datos.containsKey('tags')) req.fields['tags'] = datos['tags'];
        if (datos['imagePath'] != null &&
          File(datos['imagePath']).existsSync()) {
          req.files
          .add(await http.MultipartFile.fromPath('foto', datos['imagePath']));
          }
          return (await req.send()).statusCode == 200;
      } catch (e) {
        return false;
      }
    }

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

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => FormScreen(
            pendientePC: p,
            fotoInicialPath: fotoLocal,
            onSave: (registro) {
              // TERMINAR
              Map<String, dynamic> t = {
                'id': p.id,
                'titulo': registro.titulo,
                'detalles': registro.detalles,
                'tags': registro.tags,
                'imagePath': registro.imagePath
              };
              setState(() {
                _colaSalida.add(t);
                _listaPC.removeWhere((i) => i.id == p.id);
                if (refID != null) _fotosLocales.remove(refID);
                _fotosLocales.remove(p.id.toString());
              });
              _guardarCache();
              _sincronizarTodo(silencioso: true);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("✅ Finalizado")));
            },
            onUpdate: (registro) {
              // ACTUALIZAR
              String clave = refID ?? p.id.toString();

              if (registro.imagePath != null) {
                setState(
                  () => _fotosLocales[clave] = registro.imagePath!);
              }

              Map<String, dynamic> t = {
                'id': p.id,
                'titulo': registro.titulo,
                'detalles': registro.detalles,
                'tags': registro.tags, // Guardamos tags al actualizar
                'imagePath': registro.imagePath
              };
              setState(() => _colaEdicion.add(t));
              _guardarCache();
              _sincronizarTodo(silencioso: true);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("✅ Guardado")));
              Navigator.pop(context);
            })));
    }

    void _borrar(int id) async {
      if (await showDialog(
        context: context,
        builder: (ctx) => AlertDialog(title: const Text("¿Borrar?"), actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text("NO")),
            TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text("SÍ", style: TextStyle(color: Colors.redAccent)))
        ])) ==
        true) {
        setState(() {
          _listaPC.removeWhere((p) => p.id == id);
          _colaBorrados.add(id);
        });
        _guardarCache();
        _sincronizarTodo(silencioso: true);
        }
    }

    Future<void> _escanearQR() async {
      final codigo = await Navigator.push(
        context, MaterialPageRoute(builder: (_) => const QRScanScreen()));

      if (codigo != null && codigo is String) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('pc_ip_url', codigo);
        setState(() => _urlPC = codigo);
        _sincronizarTodo();
      }
    }

    @override
    Widget build(BuildContext context) {
      int cola = _colaSalida.length +
      _colaNuevos.length +
      _colaBorrados.length +
      _colaEdicion.length;

      return Scaffold(
        // Quitamos el AppBar porque ahora usamos el de MainScreen
        body: Column(
          children: [
            // Barra de estado de conexión personalizada
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: _urlPC == null ? Colors.red.withOpacity(0.2) : Theme.of(context).primaryColor.withOpacity(0.1),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Icon(_urlPC == null ? Icons.cloud_off : Icons.cloud_done,
                           color: _urlPC == null ? Colors.red : Colors.green),
                      const SizedBox(width: 8),
                      Text(_urlPC == null ? "Offline" : "Conectado", style: const TextStyle(fontWeight: FontWeight.bold)),
                    ],
                  ),
                  Text(cola > 0 ? "Pendientes de subir: $cola" : "Sincronizado", style: const TextStyle(fontSize: 12)),
                ],
              ),
            ),

            Expanded(
              child: _urlPC == null
              ? Center(
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.qr_code),
                  label: const Text("Vincular PC"),
                  onPressed: _escanearQR))
              : _listaPC.isEmpty
              ? const Center(child: Text("No hay tareas asignadas"))
              : ListView.builder(
                itemCount: _listaPC.length,
                itemBuilder: (ctx, i) {
                  final item = _listaPC[i];

                  String? refID = _extraerRef(item.detalles);
                  bool tieneFoto = false;
                  String? pathFoto;

                  if (refID != null && _fotosLocales.containsKey(refID)) {
                    pathFoto = _fotosLocales[refID];
                  } else if (_fotosLocales
                    .containsKey(item.id.toString())) {
                    pathFoto = _fotosLocales[item.id.toString()];
                    }

                    if (pathFoto != null && File(pathFoto).existsSync()) {
                      tieneFoto = true;
                    }

                    String limpio = item.detalles
                    .replaceAll(RegExp(r"\[FOTO:.*?\]"), "")
                    .replaceAll(RegExp(r"\[REF:.*?\]"), "")
                    .trim();

                    return Card(
                      // Sin color hardcoded
                      child: ListTile(
                        leading: tieneFoto
                        ? ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: Image.file(File(pathFoto!),
                          width: 50, height: 50, fit: BoxFit.cover))
                        : const CircleAvatar(
                          backgroundColor: Colors.orange,
                          child: Icon(Icons.warning_amber,
                                      color: Colors.white)),
                                      title: Text(item.titulo,
                                                  style: const TextStyle(fontWeight: FontWeight.bold)),
                                                  subtitle: Text(limpio, maxLines: 2),
                                                  onTap: () => _abrirGestionar(item),
                                                  trailing: IconButton(
                                                    icon: const Icon(Icons.delete, color: Colors.redAccent),
                                                    onPressed: () => _borrar(item.id)),
                      ),
                    );
                },
              ),
            ),
          ],
        ),
        floatingActionButton: FloatingActionButton.extended(
          backgroundColor: Colors.orange[800],
          icon: const Icon(Icons.add_task),
          label: const Text("AÑADIR"),
          onPressed: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => FormScreen(
                esCrearPendiente: true,
                onSave: (r) {
                  String refUnica =
                  DateTime.now().millisecondsSinceEpoch.toString();
                  if (r.imagePath != null) {
                    setState(
                      () => _fotosLocales[refUnica] = r.imagePath!);
                  }
                  String detallesConRef = "${r.detalles} [REF:$refUnica]";
                  Map<String, dynamic> t = {
                    'titulo': r.titulo,
                    'detalles': detallesConRef,
                    'tags': r.tags,
                    'imagePath': r.imagePath
                  };
                  setState(() => _colaNuevos.add(t));
                  PendientePC temp = PendientePC(
                    id: -DateTime.now().millisecondsSinceEpoch,
                    titulo: r.titulo,
                    detalles: detallesConRef);
                  setState(() => _listaPC.insert(0, temp));
                  _guardarCache();
                  _sincronizarTodo(silencioso: true);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("✅ Pendiente creado")));
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
    super.key,
    required this.onSave,
    this.onUpdate,
    this.pendientePC,
    this.registroExistente,
    this.esCrearPendiente = false,
    this.fotoInicialPath,
  });

  @override
  State<FormScreen> createState() => _FormScreenState();
}

class _FormScreenState extends State<FormScreen> {
  final _titleCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  final _tagCtrl = TextEditingController();
  String? _imagePath;

  bool _isUrgente = false;
  bool _isElectrico = false;
  bool _isMecanico = false;
  bool _isPreventivo = false;

  @override
  void initState() {
    super.initState();
    if (widget.pendientePC != null) {
      _titleCtrl.text = widget.pendientePC!.titulo;
      _descCtrl.text = widget.pendientePC!.detalles
      .replaceAll(RegExp(r"\[FOTO:.*?\]"), "")
      .replaceAll(RegExp(r"\[REF:.*?\]"), "")
      .trim();
      if (widget.fotoInicialPath != null) _imagePath = widget.fotoInicialPath;
    }
    if (widget.registroExistente != null) {
      final r = widget.registroExistente!;
      if (r.titulo.isNotEmpty) _titleCtrl.text = r.titulo;
      if (r.detalles.isNotEmpty) _descCtrl.text = r.detalles;
      if (r.imagePath != null && File(r.imagePath!).existsSync()) {
        _imagePath = r.imagePath;
      }

      // LOGICA PARA RECUPERAR TAGS
      _isUrgente = r.tags.contains("Urgente");
      _isElectrico = r.tags.contains("Eléctrico");
      _isMecanico = r.tags.contains("Mecánico");
      _isPreventivo = r.tags.contains("Preventivo");

      // Recuperar tags manuales (los que no son los predefinidos)
      List<String> tagsManuales = r.tags.split(', ')
      .where((t) => !['Urgente', 'Eléctrico', 'Mecánico', 'Preventivo'].contains(t))
      .toList();
      if (tagsManuales.isNotEmpty) {
        _tagCtrl.text = tagsManuales.join(', ');
      }
    }
  }

  Future<void> _takePhoto() async {
    try {
      final picker = ImagePicker();
      final pickedFile = await picker.pickImage(
        source: ImageSource.camera, imageQuality: 60);
      if (pickedFile != null) {
        final directory = await getApplicationDocumentsDirectory();
        final String fileName =
        'foto_${DateTime.now().millisecondsSinceEpoch}.jpg';
        final String nuevoPath = path.join(directory.path, fileName);
        await File(pickedFile.path).copy(nuevoPath);
        setState(() {
          _imagePath = nuevoPath;
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context)
      .showSnackBar(SnackBar(content: Text("❌ Error: $e")));
    }
  }

  Future<void> _openEditor() async {
    if (_imagePath == null) return;
    final bool? ok = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ImageEditorScreen(imageFile: File(_imagePath!))));
    if (ok == true) {
      setState(() {
        PaintingBinding.instance.imageCache.clear();
        PaintingBinding.instance.imageCache.clearLiveImages();
      });
    }
  }

  void _borrarFoto() {
    setState(() {
      _imagePath = null;
    });
  }

  void _guardarLocal(bool esTerminar) {
    if (_titleCtrl.text.isEmpty) return;
    List<String> l = [];
    if (_isUrgente) l.add("Urgente");
    if (_isElectrico) l.add("Eléctrico");
    if (_isMecanico) l.add("Mecánico");
    if (_isPreventivo) l.add("Preventivo");
    if (_tagCtrl.text.isNotEmpty) l.add(_tagCtrl.text.trim());

    String detallesFinales = _descCtrl.text;
    if (widget.pendientePC != null) {
      final match = RegExp(r"\[REF:(\d+)\]")
      .firstMatch(widget.pendientePC!.detalles);
      if (match != null) {
        detallesFinales += " ${match.group(0)}";
      }
    }

    Registro r = Registro(
      titulo: _titleCtrl.text,
      detalles: detallesFinales,
      tags: l.join(", "),
      imagePath: _imagePath);

    if (esTerminar) {
      widget.onSave(r);
    } else if (widget.onUpdate != null) {
      widget.onUpdate!(r);
    } else {
      widget.onSave(r);
    }

    if (widget.onUpdate == null || esTerminar) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    bool esTrabajoPC = widget.pendientePC != null;
    return Scaffold(
      appBar: AppBar(
        title: Text(esTrabajoPC ? "Gestionar Trabajo" : "Nuevo"),
        backgroundColor: Colors.blueGrey),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(children: [
            TextField(
              controller: _titleCtrl,
              decoration: const InputDecoration(labelText: "Título")),
              const SizedBox(height: 15),
              TextField(
                controller: _descCtrl,
                maxLines: 5,
                decoration: const InputDecoration(labelText: "Detalles")),
                const SizedBox(height: 15),

                const Align(alignment: Alignment.centerLeft, child: Text("Etiquetas:", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey))),
                const SizedBox(height: 5),
                Wrap(
                  spacing: 8.0,
                  children: [
                    FilterChip(
                      label: const Text('🚨 Urgente'),
                      selected: _isUrgente,
                      selectedColor: Colors.red.withOpacity(0.3),
                      onSelected: (v) => setState(() => _isUrgente = v),
                    ),
                     FilterChip(
                       label: const Text('⚡ Eléctrico'),
                       selected: _isElectrico,
                       selectedColor: Colors.blue.withOpacity(0.3),
                       onSelected: (v) => setState(() => _isElectrico = v),
                     ),
                     FilterChip(
                       label: const Text('⚙️ Mecánico'),
                       selected: _isMecanico,
                       selectedColor: Colors.orange.withOpacity(0.3),
                       onSelected: (v) => setState(() => _isMecanico = v),
                     ),
                     FilterChip(
                       label: const Text('🛡️ Preventivo'),
                       selected: _isPreventivo,
                       selectedColor: Colors.green.withOpacity(0.3),
                       onSelected: (v) => setState(() => _isPreventivo = v),
                     ),
                  ],
                ),
                TextField(
                  controller: _tagCtrl,
                  decoration: const InputDecoration(
                    labelText: "Otras etiquetas (opcional)",
                    hintText: "Ej: Rodamiento, Limpieza...",
                    isDense: true
                  ),
                ),
                const SizedBox(height: 15),
                const Divider(),

                if (_imagePath != null) ...[
                  SizedBox(
                    height: 300,
                    child: Image.file(File(_imagePath!), fit: BoxFit.contain)),
                    const SizedBox(height: 10),
                    Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                      ElevatedButton.icon(
                        icon: const Icon(Icons.edit),
                        label: const Text("DIBUJAR"),
                        onPressed: _openEditor),
                        const SizedBox(width: 10),
                        ElevatedButton.icon(
                          icon: const Icon(Icons.delete),
                          label: const Text("BORRAR"),
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                          onPressed: _borrarFoto),
                    ])
                ] else
                ElevatedButton.icon(
                  icon: const Icon(Icons.camera_alt),
                  label: const Text("AÑADIR FOTO"),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 50)),
                    onPressed: _takePhoto),

                    const SizedBox(height: 20),

                    if (esTrabajoPC) ...[
                      Row(children: [
                        Expanded(
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.blue,
                              padding: const EdgeInsets.symmetric(vertical: 15)),
                              onPressed: () => _guardarLocal(false),
                              child: const Text("ACTUALIZAR",
                                                style: TextStyle(
                                                  color: Colors.white, fontWeight: FontWeight.bold)),
                          )),
                          const SizedBox(width: 10),
                          Expanded(
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green,
                                padding: const EdgeInsets.symmetric(vertical: 15)),
                                onPressed: () => _guardarLocal(true),
                                child: const Text("TERMINAR",
                                                  style: TextStyle(
                                                    color: Colors.white, fontWeight: FontWeight.bold)),
                            )),
                      ])
                    ] else
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blueGrey,
                        minimumSize: const Size.fromHeight(50)),
                        onPressed: () => _guardarLocal(true),
                        child: Text(
                          widget.esCrearPendiente ? "GUARDAR PENDIENTE" : "GUARDAR",
                          style: const TextStyle(fontWeight: FontWeight.bold)),
                    )
          ]),
        ),
    );
  }
}

// ==========================================
// 6. UTILIDADES Y HERRAMIENTAS
// ==========================================

class QRScanScreen extends StatefulWidget {
  const QRScanScreen({super.key});

  @override
  State<QRScanScreen> createState() => _QRScanScreenState();
}

class _QRScanScreenState extends State<QRScanScreen> {
  bool _scanned = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Escanear QR del PC")),
      body: MobileScanner(
        onDetect: (capture) {
          if (_scanned) return;
          final List<Barcode> barcodes = capture.barcodes;
          for (final barcode in barcodes) {
            if (barcode.rawValue != null) {
              setState(() => _scanned = true);
              String raw = barcode.rawValue!;
              String ip = raw.replaceAll("http://", "").replaceAll("/", "");
              Navigator.pop(context, ip);
              break;
            }
          }
        },
      ),
    );
  }
}

class ImageEditorScreen extends StatefulWidget {
  final File imageFile;
  const ImageEditorScreen({super.key, required this.imageFile});

  @override
  State<ImageEditorScreen> createState() => _ImageEditorScreenState();
}

class _ImageEditorScreenState extends State<ImageEditorScreen> {
  final _controller = ImagePainterController(
    color: Colors.red,
    strokeWidth: 4.0,
    mode: PaintMode.freeStyle,
  );

  bool _guardando = false;

  @override
  void initState() {
    super.initState();
    SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  }

  @override
  void dispose() {
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.portraitDown,
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight
    ]);
    super.dispose();
  }

  Future<void> _guardarImagen() async {
    if (_guardando) return;
    setState(() => _guardando = true);

    try {
      final bytes = await _controller.exportImage();
      if (bytes != null) {
        await widget.imageFile.writeAsBytes(bytes);
        if (mounted) Navigator.pop(context, true);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error al guardar: $e"), backgroundColor: Colors.red)
      );
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async => !_guardando,
      child: Scaffold(
        backgroundColor: Colors.grey[900], // Fondo gris para edición
        appBar: AppBar(
          backgroundColor: Colors.grey[900],
          iconTheme: const IconThemeData(color: Colors.white),
          title: Text(_guardando ? "Guardando..." : "Dibujar / Marcar",
                      style: const TextStyle(color: Colors.white)),
                      actions: [
                        if (_guardando)
                          const Padding(
                            padding: EdgeInsets.all(16.0),
                            child: SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.greenAccent))
                          )
                          else
                            IconButton(
                              icon: const Icon(Icons.check, color: Colors.greenAccent, size: 30),
                              onPressed: _guardarImagen,
                            )
                      ],
        ),
        body: _guardando
        ? const Center(child: CircularProgressIndicator(color: Colors.greenAccent))
        : ImagePainter.file(widget.imageFile, controller: _controller, scalable: true),
      ),
    );
  }
}
