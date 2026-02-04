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

          // --- TEMA CLARO ---
          theme: ThemeData.light().copyWith(
            scaffoldBackgroundColor: const Color(0xFFF5F5F5), // Gris muy claro
            appBarTheme: const AppBarTheme(
              backgroundColor: Color(0xFF37474F), // BlueGrey 800
              foregroundColor: Colors.white,
            ),
            cardColor: Colors.white,
            // Definimos un esquema de color para que los botones se vean bien
            colorScheme: const ColorScheme.light(
              primary: Color(0xFF37474F),
              secondary: Colors.orangeAccent,
            ),
            bottomNavigationBarTheme: const BottomNavigationBarThemeData(
              backgroundColor: Color(0xFF37474F),
              selectedItemColor: Colors.white,
              unselectedItemColor: Colors.white60,
            ),
          ),

          // --- TEMA OSCURO CORREGIDO ---
          darkTheme: ThemeData.dark().copyWith(
            // Fondo casi negro (Estándar Material)
            scaffoldBackgroundColor: const Color(0xFF121212),
            appBarTheme: const AppBarTheme(
              backgroundColor: Color(0xFF1F1F1F),
              foregroundColor: Colors.white
            ),
            // Tarjetas más claras que el fondo para destacar (Surface color)
            cardColor: const Color(0xFF2C2C2C),
            dividerColor: Colors.grey[700],
            colorScheme: const ColorScheme.dark(
              primary: Color(0xFF90CAF9), // Azul claro para acentos
              secondary: Colors.orangeAccent,
              surface: Color(0xFF2C2C2C),
            ),
            bottomNavigationBarTheme: const BottomNavigationBarThemeData(
              backgroundColor: Color(0xFF1F1F1F),
              selectedItemColor: Color(0xFF90CAF9),
              unselectedItemColor: Colors.grey,
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
  int? id; // Añadido ID para edición histórica
  String titulo, detalles, tags;
  String? imagePath; // Ruta local
  String? serverImageName; // Nombre fichero en servidor (para descarga)

  Registro({
    this.id,
    required this.titulo,
    required this.detalles,
    required this.tags,
    this.imagePath,
    this.serverImageName
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'titulo': titulo,
    'detalles': detalles,
    'tags': tags,
    'imagePath': imagePath,
    'serverImageName': serverImageName
  };

  factory Registro.fromJson(Map<String, dynamic> json) => Registro(
    id: json['id'],
    titulo: json['titulo'],
    detalles: json['detalles'],
    tags: json['tags'],
    imagePath: json['imagePath'],
    serverImageName: json['serverImageName']
  );
}

class PendientePC {
  int id;
  String titulo, detalles;
  PendientePC({required this.id, required this.titulo, required this.detalles});
  factory PendientePC.fromJson(Map<String, dynamic> json) => PendientePC(
    id: json['id'], titulo: json['titulo'], detalles: json['detalles']);
}

class AvisoPC {
  int id;
  String titulo, frecuencia, rango, estado, color;

  AvisoPC({
    required this.id, required this.titulo, required this.frecuencia,
    required this.rango, required this.estado, required this.color
  });

  factory AvisoPC.fromJson(Map<String, dynamic> json) => AvisoPC(
    id: json['id'],
    titulo: json['titulo'],
    frecuencia: json['frecuencia'],
    rango: json['rango'],
    estado: json['estado'],
    color: json['color']
  );
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

  // Función para cambiar pestaña programáticamente
  void _irAPestana(int index) {
    setState(() {
      _indiceActual = index;
    });
  }

  // Lista dinámica para poder pasar la función
  late final List<Widget> _pantallas;

  @override
  void initState() {
    super.initState();
    _pantallas = [
      TabDashboard(onNavigate: _irAPestana), // Pasamos la función al dashboard
      const TabMisRegistros(),
      const TabPendientesPC(),
      const TabAvisos(),     // NUEVA PESTAÑA (Índice 3)
      const TabHistorial(),  // Historial pasa al índice 4
    ];
  }

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

    // Títulos dinámicos
    String titulo = "MantPro";
    switch(_indiceActual) {
      case 0: titulo = "Dashboard"; break;
      case 1: titulo = "Mis Registros Locales"; break;
      case 2: titulo = "Pendientes"; break;
      case 3: titulo = "Avisos Recurrentes"; break;
      case 4: titulo = "Historial Completo"; break;
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(titulo),
        actions: [
          IconButton(icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode), onPressed: _toggleTheme),
        ],
      ),
      body: IndexedStack(index: _indiceActual, children: _pantallas),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _indiceActual,
        type: BottomNavigationBarType.fixed,
        onTap: (index) => setState(() => _indiceActual = index),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: "Inicio"),
          BottomNavigationBarItem(icon: Icon(Icons.edit_note), label: "Local"),
          BottomNavigationBarItem(icon: Icon(Icons.checklist), label: "Pendientes"),
          BottomNavigationBarItem(icon: Icon(Icons.warning_amber), label: "Avisos"), // Nueva Icono
          BottomNavigationBarItem(icon: Icon(Icons.history), label: "Historial"),
        ],
      ),
    );
  }
}

// ==========================================
// PESTAÑA 0: DASHBOARD (NUEVA)
// ==========================================
class TabDashboard extends StatefulWidget {
  final Function(int) onNavigate; // Recibimos la función
  const TabDashboard({super.key, required this.onNavigate});

  @override
  State<TabDashboard> createState() => _TabDashboardState();
}

class _TabDashboardState extends State<TabDashboard> {
  Map<String, dynamic> _stats = {"pendientes": 0, "registros_mes": 0, "avisos_total": 0};
  bool _cargando = false;
  String? _urlPC;

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
    setState(() => _cargando = true);
    try {
      final res = await http.get(Uri.parse("http://$_urlPC/api/dashboard")).timeout(const Duration(seconds: 3));
      if (res.statusCode == 200) {
        setState(() => _stats = json.decode(res.body));
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('dashboard_cache', res.body);
      }
    } catch (e) { } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Widget _buildCard(String title, String count, IconData icon, Color color, int targetTabIndex) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      // Usamos InkWell para detectar el toque y hacer el efecto visual
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => widget.onNavigate(targetTabIndex), // NAVEGACIÓN AQUÍ
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 40, color: color),
              const SizedBox(height: 10),
              Flexible(
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Text(count, style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color)),
                ),
              ),
              const SizedBox(height: 5),
              Text(title, style: const TextStyle(fontSize: 14, color: Colors.grey), textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_urlPC == null && _stats['pendientes'] == 0) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.link_off, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text("PC No Vinculado"),
            TextButton(
              onPressed: () async {
                final ip = await Navigator.push(context, MaterialPageRoute(builder: (_) => const QRScanScreen()));
                if (ip != null) {
                  final prefs = await SharedPreferences.getInstance();
                  await prefs.setString('pc_ip_url', ip);
                  _inicializarDatos();
                }
              },
              child: const Text("Vincular Ahora"))
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _cargarStatsOnline,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("Estado Planta", style: Theme.of(context).textTheme.headlineSmall),
              _cargando
              ? const SizedBox(width: 15, height: 15, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.cloud_done, size: 18, color: Colors.green)
            ],
          ),
          const SizedBox(height: 20),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            physics: const NeverScrollableScrollPhysics(),
            children: [
              // Mapeo de Índices:
              // 2 = Pendientes
              // 4 = Historial
              // 3 = Avisos
              _buildCard("Pendientes", "${_stats['pendientes']}", Icons.assignment_late, Colors.orange, 2),
              _buildCard("Registros Mes", "${_stats['registros_mes']}", Icons.calendar_today, Colors.blue, 4),
              _buildCard("Avisos Config.", "${_stats['avisos_total']}", Icons.alarm, Colors.purple, 3),
              _buildCard("Conexión", _cargando ? "..." : (_urlPC != null ? "OK" : "No"), Icons.wifi, Colors.green, 0), // Este se queda en dashboard (0)
            ],
          ),
        ],
      ),
    );
  }
}

// ==========================================
// PESTAÑA 3: HISTORIAL (NUEVA)
// ==========================================
class TabHistorial extends StatefulWidget {
  const TabHistorial({super.key});
  @override
  State<TabHistorial> createState() => _TabHistorialState();
}

class _TabHistorialState extends State<TabHistorial> {
  List<Registro> _registros = [];

  // COLA OFFLINE PARA HISTORIAL
  // Guardamos: { "id": "1", "detalles": "Texto...", "tags": "...", "fotoPath": "/ruta/local/foto.jpg" }
  List<Map<String, dynamic>> _colaEdiciones = [];

  bool _cargando = false;
  String? _urlPC;
  final TextEditingController _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _inicializarHistorial();
  }

  Future<void> _inicializarHistorial() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() => _urlPC = prefs.getString('pc_ip_url'));

    // 1. Cargar cola de ediciones pendientes
    String? colaJson = prefs.getString('historial_cola_ediciones');
    if (colaJson != null) {
      _colaEdiciones = List<Map<String, dynamic>>.from(json.decode(colaJson));
    }

    // 2. Cargar caché visual
    String? cache = prefs.getString('historial_cache');
    if (cache != null) {
      final List<dynamic> data = json.decode(cache);
      setState(() {
        _registros = data.map((item) => Registro.fromJson(item)).toList();
      });
      // APLICAR CAMBIOS PENDIENTES SOBRE LA VISTA (Optimistic UI)
      _aplicarCambiosVisuales();
    }

    // 3. Si hay red, sincronizar y buscar
    if (_urlPC != null) {
      await _sincronizarEdiciones(); // Primero subimos lo pendiente
      _buscar(""); // Luego bajamos lo nuevo
    }
  }

  Future<void> _guardarCola() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('historial_cola_ediciones', json.encode(_colaEdiciones));
  }

  // Aplica visualmente las ediciones pendientes sobre la lista cargada
  void _aplicarCambiosVisuales() {
    for (var edicion in _colaEdiciones) {
      int index = _registros.indexWhere((r) => r.id.toString() == edicion['id']);
      if (index != -1) {
        // Actualizamos el objeto en memoria para que el usuario lo vea "guardado"
        Registro original = _registros[index];
        _registros[index] = Registro(
          id: original.id,
          titulo: original.titulo, // Mantenemos fecha
          detalles: edicion['detalles'],
          tags: edicion['tags'],
          serverImageName: original.serverImageName, // Mantenemos ref antigua hasta sincronizar
          imagePath: edicion['fotoPath'] ?? original.imagePath // Usamos la foto nueva local si hay
        );
      }
    }
  }

  Future<void> _sincronizarEdiciones() async {
    if (_urlPC == null || _colaEdiciones.isEmpty) return;

    List<Map<String, dynamic>> subidosOk = [];

    for (var edicion in _colaEdiciones) {
      try {
        var uri = Uri.parse("http://$_urlPC/api/editar_historial");
        var req = http.MultipartRequest('POST', uri);
        req.fields['id'] = edicion['id'];
        req.fields['detalles'] = edicion['detalles'];
        req.fields['tags'] = edicion['tags'];

        String? fotoPath = edicion['fotoPath'];
        if (fotoPath != null && File(fotoPath).existsSync()) {
          req.files.add(await http.MultipartFile.fromPath('foto', fotoPath));
        }

        var res = await req.send();
        if (res.statusCode == 200) {
          subidosOk.add(edicion);
        }
      } catch (e) {
        print("Error subiendo edición historial: $e");
      }
    }

    if (subidosOk.isNotEmpty) {
      setState(() {
        for (var s in subidosOk) _colaEdiciones.remove(s);
      });
        await _guardarCola();
    }
  }

  Future<void> _buscar(String query) async {
    // Si no hay URL, solo filtramos localmente lo que ya tenemos en caché
    if (_urlPC == null) {
      // Podríamos implementar filtrado local aquí, pero por ahora mostramos lo cacheado
      return;
    }

    setState(() => _cargando = true);
    try {
      final res = await http.get(Uri.parse("http://$_urlPC/api/historial?q=$query")).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List<dynamic> data = json.decode(res.body);

        List<Registro> nuevosRegistros = data.map((item) => Registro(
          id: item['id'],
          titulo: "${item['fecha']}",
          detalles: item['descripcion'],
          tags: item['tags'],
          serverImageName: item['foto'],
          imagePath: item['raw_desc']
        )).toList();

        // Cachear fotos nuevas (Lógica Offline de Historial que ya tenías)
        final directory = await getApplicationDocumentsDirectory();
        for (var r in nuevosRegistros) {
          if (r.serverImageName != null) {
            final String filePath = path.join(directory.path, r.serverImageName!);
            if (!File(filePath).existsSync()) {
              try {
                var imgRes = await http.get(Uri.parse("http://$_urlPC/api/foto/${r.serverImageName}"));
                if (imgRes.statusCode == 200) await File(filePath).writeAsBytes(imgRes.bodyBytes);
              } catch (e) {}
            }
          }
        }

        setState(() => _registros = nuevosRegistros);

        // Re-aplicar cambios pendientes que aun no se han subido (para no machacarlos con la versión vieja del server)
        _aplicarCambiosVisuales();

        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('historial_cache', json.encode(nuevosRegistros.map((r) => r.toJson()).toList()));
      }
    } catch (e) {
      // Error silencioso, mantenemos caché
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  void _editarHistorial(Registro reg) async {
    // Recuperar descripción RAW y Foto Local
    String rawDesc = reg.imagePath ?? reg.detalles;
    String? localPhotoForEdit;

    // 1. Buscar foto localmente (Prioridad: Edición pendiente > Caché descargado)

    // A) ¿Tiene una edición pendiente con foto nueva?
    var edicionPendiente = _colaEdiciones.firstWhere(
      (e) => e['id'] == reg.id.toString(),
      orElse: () => {}
    );

    if (edicionPendiente.isNotEmpty && edicionPendiente['fotoPath'] != null) {
      localPhotoForEdit = edicionPendiente['fotoPath'];
    }
    // B) Si no, ¿tiene foto del servidor cacheada?
    else if (reg.serverImageName != null) {
      final directory = await getApplicationDocumentsDirectory();
      final String filePath = path.join(directory.path, reg.serverImageName!);
      if (File(filePath).existsSync()) {
        localPhotoForEdit = filePath;
      } else if (_urlPC != null) {
        // Intento de descarga al vuelo si hay red
        try {
          var response = await http.get(Uri.parse("http://$_urlPC/api/foto/${reg.serverImageName}"));
          if (response.statusCode == 200) {
            await File(filePath).writeAsBytes(response.bodyBytes);
            localPhotoForEdit = filePath;
          }
        } catch (e) {}
      }
    }

    Registro regParaForm = Registro(
      id: reg.id,
      titulo: "",
      detalles: rawDesc,
      tags: reg.tags,
      imagePath: localPhotoForEdit
    );

    await Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(
      registroExistente: regParaForm,
      esHistorial: true,
      onSave: (registroEditado) async {
        // --- LÓGICA DE GUARDADO OFFLINE ---

        // 1. Guardar en Cola Local
        Map<String, dynamic> nuevaEdicion = {
          'id': reg.id.toString(),
          'detalles': registroEditado.detalles,
          'tags': registroEditado.tags,
          'fotoPath': registroEditado.imagePath // Guardamos la ruta de la nueva foto
        };

        // Si ya había una edición para este ID, la reemplazamos
        int idx = _colaEdiciones.indexWhere((e) => e['id'] == reg.id.toString());
        if (idx != -1) {
          _colaEdiciones[idx] = nuevaEdicion;
        } else {
          _colaEdiciones.add(nuevaEdicion);
        }

        await _guardarCola();

        // 2. Actualizar UI inmediatamente
        setState(() {
          _aplicarCambiosVisuales();
        });

        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Guardado (Sincronizará al conectar)")));

        // 3. Intentar subir si hay red
        _sincronizarEdiciones();
      }
    )));
  }

  Future<String> getLocalPath(String filename) async {
    final directory = await getApplicationDocumentsDirectory();
    return path.join(directory.path, filename);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Barra de estado de cola
        if (_colaEdiciones.isNotEmpty)
          Container(
            width: double.infinity,
            color: Colors.orangeAccent,
            padding: const EdgeInsets.all(8),
            child: Text(
              "${_colaEdiciones.length} ediciones pendientes de subir",
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),

          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              controller: _searchCtrl,
              decoration: InputDecoration(
                hintText: "Buscar en historial...",
                suffixIcon: IconButton(icon: const Icon(Icons.search), onPressed: () => _buscar(_searchCtrl.text)),
                border: const OutlineInputBorder(),
                filled: _urlPC == null,
                fillColor: _urlPC == null ? Colors.red.withOpacity(0.05) : null,
              ),
              onSubmitted: _buscar,
            ),
          ),
          Expanded(
            child: _cargando
            ? const Center(child: CircularProgressIndicator())
            : _registros.isEmpty
            ? const Center(child: Text("Sin historial visible"))
            : ListView.builder(
              itemCount: _registros.length,
              itemBuilder: (ctx, i) {
                final r = _registros[i];

                // LÓGICA DE ICONO:
                // Prioridad: Foto Local (recién editada) > Foto Servidor (cacheada) > Icono Texto
                Widget imageWidget;

                if (r.imagePath != null && File(r.imagePath!).existsSync() && !r.imagePath!.contains("[")) {
                  // Caso: Acabamos de editar y poner foto local (y aun no se sube)
                  // Nota: comprobamos !contains("[") porque a veces usamos imagePath para guardar el raw_desc
                  imageWidget = Image.file(File(r.imagePath!), width: 50, height: 50, fit: BoxFit.cover);
                }
                else if (r.serverImageName != null) {
                  // Caso: Foto del servidor
                  imageWidget = FutureBuilder<String>(
                    future: getLocalPath(r.serverImageName!),
                    builder: (context, snapshot) {
                      if (snapshot.hasData && File(snapshot.data!).existsSync()) {
                        return Image.file(File(snapshot.data!), width: 50, height: 50, fit: BoxFit.cover);
                      } else if (_urlPC != null) {
                        return Image.network("http://$_urlPC/api/foto/${r.serverImageName}",
                                             width: 50, height: 50, fit: BoxFit.cover,
                                             errorBuilder: (c, e, s) => const Icon(Icons.broken_image, color: Colors.redAccent));
                      } else {
                        return const Icon(Icons.no_photography, color: Colors.grey);
                      }
                    }
                  );
                } else {
                  imageWidget = const Icon(Icons.article, color: Colors.blueGrey);
                }

                // ¿Está este registro pendiente de subida?
                bool pendiente = _colaEdiciones.any((e) => e['id'] == r.id.toString());

                return Card(
                  color: pendiente ? Colors.orange.withOpacity(0.1) : null, // Fondo naranjita si está pendiente
                  margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  child: ListTile(
                    leading: ClipRRect(borderRadius: BorderRadius.circular(4), child: SizedBox(width: 50, height: 50, child: Center(child: imageWidget))),
                    title: Text(r.detalles, maxLines: 2, overflow: TextOverflow.ellipsis),
                    subtitle: Text("${r.titulo} | ${r.tags}"),
                    trailing: Icon(
                      pendiente ? Icons.cloud_upload : Icons.edit,
                      size: 20,
                      color: pendiente ? Colors.orange : Colors.blueGrey
                    ),
                    onTap: () => _editarHistorial(r),
                  ),
                );
              },
            )
          )
      ],
    );
  }
}

// ==========================================
// PESTAÑA 1: MIS REGISTROS (LOCALES)
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
    final uri = Uri.parse("http://$urlUsar/api/upload");
    List<Registro> enviados = [];

    for (var item in _pendientes) {
      try {
        var req = http.MultipartRequest('POST', uri);
        req.fields['titulo'] = item.titulo;
        req.fields['detalles'] = item.detalles;
        req.fields['tags'] = item.tags;
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
        setState(() {
          for (var e in enviados) _pendientes.remove(e);
        });
          _guardarDatos();
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("✅ ${enviados.length} enviados")));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            color: Theme.of(context).appBarTheme.backgroundColor?.withOpacity(0.1),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                if (_urlPC != null)
                  TextButton.icon(
                    icon: _cargando ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.sync),
                    label: const Text("Sincronizar"),
                    onPressed: () => _sincronizar(),
                  ),
                  IconButton(
                    icon: const Icon(Icons.qr_code),
                    tooltip: "Cambiar PC",
                    onPressed: () async {
                      final ip = await Navigator.push(context, MaterialPageRoute(builder: (_) => const QRScanScreen()));
                      if (ip != null) _sincronizar(ip);
                    }),
              ],
            ),
          ),
          Expanded(
            child: _pendientes.isEmpty
            ? const Center(child: Text("Sin registros locales", style: TextStyle(color: Colors.grey)))
            : ListView.builder(
              itemCount: _pendientes.length,
              itemBuilder: (ctx, i) {
                final item = _pendientes[i];
                File? f = item.imagePath != null ? File(item.imagePath!) : null;
                return Card(
                  child: ListTile(
                    leading: f != null && f.existsSync()
                    ? Image.file(f, width: 40, height: 40, fit: BoxFit.cover)
                    : const Icon(Icons.build),
                    title: Text(item.titulo, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text(item.detalles, maxLines: 1),
                    trailing: IconButton(icon: const Icon(Icons.delete, color: Colors.redAccent), onPressed: () => _confirmarBorrado(i)),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(onSave: (r) => _editarRegistro(i, r), registroExistente: item))),
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
        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(onSave: _addRegistro)))),
    );
  }
}

// ==========================================
// PESTAÑA 2: TRABAJOS PENDIENTES PC
// ==========================================
class TabPendientesPC extends StatefulWidget {
  const TabPendientesPC({super.key});
  @override
  State<TabPendientesPC> createState() => _TabPendientesPCState();
}

class _TabPendientesPCState extends State<TabPendientesPC> {
  List<PendientePC> _listaPC = [];

  // --- COLAS DE SINCRONIZACIÓN ---
  List<Map<String, dynamic>> _colaSalida = [];   // Completar
  List<Map<String, dynamic>> _colaNuevos = [];   // Crear nuevos
  List<Map<String, dynamic>> _colaEdiciones = []; // Editar existentes (NUEVA MEJORA)
  List<int> _colaBorrados = [];                  // Borrar

  // Mapa de fotos locales (ID o REF -> Ruta Archivo)
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
        _listaPC = (json.decode(l) as List).map((i) => PendientePC.fromJson(i)).toList();
      }

      String? c = prefs.getString('cola_salida');
      if (c != null) _colaSalida = List<Map<String, dynamic>>.from(json.decode(c));

      String? n = prefs.getString('cola_nuevos');
      if (n != null) _colaNuevos = List<Map<String, dynamic>>.from(json.decode(n));

      String? e = prefs.getString('cola_ediciones'); // Nombre corregido a plural para consistencia
      if (e != null) _colaEdiciones = List<Map<String, dynamic>>.from(json.decode(e));

      String? b = prefs.getString('cola_borrados');
      if (b != null) _colaBorrados = List<int>.from(json.decode(b));

      String? f = prefs.getString('fotos_locales_map');
      if (f != null) _fotosLocales = Map<String, String>.from(json.decode(f));
    });

      // IMPORTANTE: Aplicar visualmente las ediciones pendientes (Optimistic UI)
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

  // Truco de Magia: Modificamos la lista en memoria con los cambios pendientes
  void _aplicarEdicionesVisuales() {
    for (var edicion in _colaEdiciones) {
      int index = _listaPC.indexWhere((p) => p.id.toString() == edicion['id']);
      if (index != -1) {
        _listaPC[index] = PendientePC(
          id: _listaPC[index].id,
          titulo: edicion['titulo'],
          detalles: edicion['detalles'] // Aquí ya vendrá con la nueva [REF] o [FOTO] si se añadió
        );
      }
    }
  }

  Future<String?> _descargarYCachearFoto(String nombreFoto) async {
    try {
      final directory = await getApplicationDocumentsDirectory();
      final String filePath = path.join(directory.path, nombreFoto);
      if (File(filePath).existsSync()) return filePath;

      if (_urlPC != null) {
        final response = await http.get(Uri.parse("http://$_urlPC/api/foto/$nombreFoto")).timeout(const Duration(seconds: 10));
        if (response.statusCode == 200) {
          final file = File(filePath);
          await file.writeAsBytes(response.bodyBytes);
          return filePath;
        }
      }
    } catch (e) { print(e); }
    return null;
  }

  Future<void> _sincronizarTodo({bool silencioso = false}) async {
    if (_urlPC == null) return;
    if (!silencioso) setState(() => _cargando = true);

    // 1. SUBIDAS
    List<int> borradosOk = [];
    for (var id in _colaBorrados) { if (await _apiPost('eliminar_pendiente', {'id': id.toString()})) borradosOk.add(id); }
    if (borradosOk.isNotEmpty) { setState(() { for (var id in borradosOk) _colaBorrados.remove(id); }); }

    List<Map<String, dynamic>> nuevosOk = [];
    for (var t in _colaNuevos) { if (await _apiMultipart('agregar_pendiente', t)) nuevosOk.add(t); }
    if (nuevosOk.isNotEmpty) { setState(() { for (var t in nuevosOk) _colaNuevos.remove(t); }); }

    List<Map<String, dynamic>> edicionOk = [];
    for (var t in _colaEdiciones) { if (await _apiMultipart('editar_pendiente', t)) edicionOk.add(t); }
    if (edicionOk.isNotEmpty) { setState(() { for (var t in edicionOk) _colaEdiciones.remove(t); }); }

    List<Map<String, dynamic>> salidaOk = [];
    for (var t in _colaSalida) { if (await _apiMultipart('completar_pendiente', t)) salidaOk.add(t); }
    if (salidaOk.isNotEmpty) { setState(() { for (var t in salidaOk) _colaSalida.remove(t); }); }

    await _guardarCache();

    // 2. DESCARGAS
    try {
      final res = await http.get(Uri.parse("http://$_urlPC/api/pendientes")).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List<dynamic> datos = json.decode(res.body);
        List<PendientePC> nuevosPendientes = datos.map((item) => PendientePC.fromJson(item)).toList();

        // Descarga de fotos
        for (var p in nuevosPendientes) {
          String? fotoServer = _obtenerFotoServer(p);
          if (fotoServer != null) {
            String? rutaLocal = await _descargarYCachearFoto(fotoServer);
            if (rutaLocal != null) {
              setState(() => _fotosLocales[p.id.toString()] = rutaLocal);
            }
          }
        }

        setState(() => _listaPC = nuevosPendientes);

        // RE-APLICAR EDICIONES PENDIENTES (Por si falló la subida pero la descarga funcionó)
        _aplicarEdicionesVisuales();

        await _guardarCache();
      }
    } catch (e) { /* Error red */ }

    if (!silencioso && mounted) setState(() => _cargando = false);
  }

  Future<bool> _apiPost(String endpoint, Map<String, String> body) async {
    try { return (await http.post(Uri.parse("http://$_urlPC/api/$endpoint"), body: body)).statusCode == 200; } catch (e) { return false; }
  }

  Future<bool> _apiMultipart(String endpoint, Map<String, dynamic> datos) async {
    try {
      var req = http.MultipartRequest('POST', Uri.parse("http://$_urlPC/api/$endpoint"));
      if (datos.containsKey('id')) req.fields['id'] = datos['id'].toString();
      req.fields['titulo'] = datos['titulo'];
      req.fields['detalles'] = datos['detalles'];
      // Nota: Pendientes no usa tags en edición normalmente, pero lo enviamos por si acaso
      if (datos.containsKey('tags')) req.fields['tags'] = datos['tags'];
      if (datos['imagePath'] != null && File(datos['imagePath']).existsSync()) {
        req.files.add(await http.MultipartFile.fromPath('foto', datos['imagePath']));
      }
      return (await req.send()).statusCode == 200;
    } catch (e) { return false; }
  }

  String? _extraerRef(String texto) { final match = RegExp(r"\[REF:(\d+)\]").firstMatch(texto); return match?.group(1); }

  String? _obtenerFotoServer(PendientePC p) {
    final match = RegExp(r"\[FOTO:\s*(.*?)\]").firstMatch(p.detalles);
    if (match != null) return match.group(1)!.trim();
    return null;
  }

  String? _obtenerRutaFoto(PendientePC p) {
    String? refID = _extraerRef(p.detalles);
    if (refID != null && _fotosLocales.containsKey(refID)) return _fotosLocales[refID];
    if (_fotosLocales.containsKey(p.id.toString())) return _fotosLocales[p.id.toString()];
    return null;
  }

  void _abrirGestionar(PendientePC p) async {
    String? fotoLocal = _obtenerRutaFoto(p);
    String? fotoServer = _obtenerFotoServer(p);
    if (fotoLocal != null && !File(fotoLocal).existsSync()) fotoLocal = null;

    Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(
      pendientePC: p,
      fotoInicialPath: fotoLocal,
      serverImageName: fotoServer,
      urlPC: _urlPC,
      onSave: (registro) {
        // COMPLETAR TAREA
        String? refID = _extraerRef(p.detalles);
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
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Tarea completada")));
      },
      onUpdate: (registro) {
        // EDITAR TAREA (Offline Friendly)
        String? refID = _extraerRef(p.detalles);
        String clave = refID ?? p.id.toString();

        // 1. Guardar foto nueva localmente
        if (registro.imagePath != null) {
          setState(() => _fotosLocales[clave] = registro.imagePath!);
        }

        // 2. Cola de subida
        Map<String, dynamic> t = {
          'id': p.id,
          'titulo': registro.titulo,
          'detalles': registro.detalles,
          'tags': registro.tags,
          'imagePath': registro.imagePath
        };

        // 3. ACTUALIZAR LISTA LOCAL INMEDIATAMENTE (Optimistic UI)
        setState(() {
          // Si ya había una edición pendiente para este ID, la reemplazamos
          _colaEdiciones.removeWhere((e) => e['id'] == p.id.toString());
          _colaEdiciones.add(t);

          // Refrescar objeto visual
          int idx = _listaPC.indexWhere((i) => i.id == p.id);
          if (idx != -1) {
            _listaPC[idx] = PendientePC(
              id: p.id,
              titulo: registro.titulo,
              detalles: registro.detalles
            );
          }
        });

        _guardarCache();
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ Guardado")));
        _sincronizarTodo(silencioso: true); // Intentar subir
        Navigator.pop(context); // Volver
      })));
  }

  void _borrar(int id) async {
    if (await showDialog(context: context, builder: (ctx) => AlertDialog(
      title: const Text("¿Borrar?"),
      content: const Text("Se eliminará del PC."),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("NO")),
        TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("SÍ", style: TextStyle(color: Colors.redAccent)))
      ])) == true) {
      setState(() {
        _listaPC.removeWhere((p) => p.id == id);
        _colaBorrados.add(id);
      });
    _guardarCache();
    _sincronizarTodo(silencioso: true);
      }
  }

  Future<void> _escanearQR() async {
    final codigo = await Navigator.push(context, MaterialPageRoute(builder: (_) => const QRScanScreen()));
    if (codigo != null && codigo is String) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('pc_ip_url', codigo);
      setState(() => _urlPC = codigo);
      _sincronizarTodo();
    }
  }

  @override
  Widget build(BuildContext context) {
    int cola = _colaSalida.length + _colaNuevos.length + _colaBorrados.length + _colaEdiciones.length;
    bool offlineMode = _urlPC == null;

    return Scaffold(
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: offlineMode ? Colors.red.withOpacity(0.15) : Colors.green.withOpacity(0.15),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(children: [
                  Icon(offlineMode ? Icons.cloud_off : Icons.cloud_done, color: offlineMode ? Colors.red : Colors.green, size: 20),
                  const SizedBox(width: 8),
                  Text(offlineMode ? "Sin Vinculación" : (_cargando ? "Sincronizando..." : "Conectado"), style: const TextStyle(fontWeight: FontWeight.bold))
                ]),
                if (cola > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(color: Colors.orange, borderRadius: BorderRadius.circular(10)),
                    child: Text("Cola: $cola", style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                  )
              ],
            ),
          ),
          Expanded(
            child: _listaPC.isEmpty
            ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
              const Icon(Icons.assignment_turned_in, size: 60, color: Colors.grey),
              const SizedBox(height: 10),
              const Text("No hay tareas pendientes"),
              if (offlineMode) TextButton.icon(icon: const Icon(Icons.qr_code), label: const Text("Vincular PC"), onPressed: _escanearQR)
            ]))
            : ListView.builder(
              itemCount: _listaPC.length,
              itemBuilder: (ctx, i) {
                final item = _listaPC[i];
                String? fotoLocal = _obtenerRutaFoto(item);
                String? fotoServer = _obtenerFotoServer(item);
                String limpio = item.detalles.replaceAll(RegExp(r"\[FOTO:.*?\]"), "").replaceAll(RegExp(r"\[REF:.*?\]"), "").trim();
                if (limpio.isEmpty) limpio = "Sin detalles";

                // Icono
                Widget leadingIcon;
                if (fotoLocal != null) {
                  leadingIcon = Image.file(File(fotoLocal), width: 50, height: 50, fit: BoxFit.cover);
                } else if (fotoServer != null) {
                  leadingIcon = Container(width: 50, height: 50, color: Colors.blue.withOpacity(0.1), child: const Icon(Icons.cloud_download, color: Colors.blue));
                } else {
                  leadingIcon = CircleAvatar(backgroundColor: Theme.of(context).colorScheme.secondary.withOpacity(0.2), child: Icon(Icons.build, color: Theme.of(context).colorScheme.secondary));
                }

                // Check si está editado y pendiente de subir
                bool isEdited = _colaEdiciones.any((e) => e['id'] == item.id.toString());

                return Card(
                  margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  child: ListTile(
                    leading: ClipRRect(borderRadius: BorderRadius.circular(4), child: leadingIcon),
                    title: Text(item.titulo, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text(limpio, maxLines: 2, overflow: TextOverflow.ellipsis),
                    onTap: () => _abrirGestionar(item),
                    trailing: isEdited
                    ? const Icon(Icons.cloud_upload, color: Colors.orange) // Icono si está pendiente de subir
                    : IconButton(icon: const Icon(Icons.delete, color: Colors.grey), onPressed: () => _borrar(item.id)),
                  ),
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: Theme.of(context).colorScheme.secondary,
        foregroundColor: Colors.white,
          icon: const Icon(Icons.add_task),
          label: const Text("AÑADIR"),
          onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FormScreen(esCrearPendiente: true, onSave: (r) {
            String refUnica = DateTime.now().millisecondsSinceEpoch.toString();
            if (r.imagePath != null) setState(() => _fotosLocales[refUnica] = r.imagePath!);
            String detallesConRef = "${r.detalles} [REF:$refUnica]";
            Map<String, dynamic> t = {'titulo': r.titulo, 'detalles': detallesConRef, 'tags': r.tags, 'imagePath': r.imagePath};
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
  final bool esHistorial; // NUEVO
  final String? fotoInicialPath;
  final String? serverImageName; // NUEVO
  final String? urlPC; // NUEVO

  const FormScreen({
    super.key,
    required this.onSave,
    this.onUpdate,
    this.pendientePC,
    this.registroExistente,
    this.esCrearPendiente = false,
    this.esHistorial = false,
    this.fotoInicialPath,
    this.serverImageName,
    this.urlPC,
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
    // 1. CARGA DESDE PENDIENTE PC
    if (widget.pendientePC != null) {
      _titleCtrl.text = widget.pendientePC!.titulo;
      _descCtrl.text = widget.pendientePC!.detalles.replaceAll(RegExp(r"\[FOTO:.*?\]"), "").replaceAll(RegExp(r"\[REF:.*?\]"), "").trim();
      if (widget.fotoInicialPath != null) _imagePath = widget.fotoInicialPath;
    }
    // 2. CARGA DESDE REGISTRO LOCAL O HISTORIAL
    if (widget.registroExistente != null) {
      final r = widget.registroExistente!;
      if (r.titulo.isNotEmpty) _titleCtrl.text = r.titulo;

      // Limpieza adicional por si acaso viene sucio del historial
      String d = r.detalles.replaceAll(RegExp(r"\[FOTO:.*?\]"), "").replaceAll(RegExp(r"\[REF:.*?\]"), "").trim();
      _descCtrl.text = d;

      if (r.imagePath != null && File(r.imagePath!).existsSync()) {
        _imagePath = r.imagePath;
      }

      _isUrgente = r.tags.contains("Urgente");
      _isElectrico = r.tags.contains("Eléctrico");
      _isMecanico = r.tags.contains("Mecánico");
      _isPreventivo = r.tags.contains("Preventivo");

      List<String> tagsManuales = r.tags.split(', ').where((t) => !['Urgente', 'Eléctrico', 'Mecánico', 'Preventivo'].contains(t)).toList();
      if (tagsManuales.isNotEmpty) _tagCtrl.text = tagsManuales.join(', ');
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
        setState(() => _imagePath = nuevoPath);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("❌ Error: $e")));
    }
  }

  // Función para descargar y ver la foto del servidor si no tenemos local
  Future<void> _descargarParaVer() async {
    if (widget.serverImageName != null && widget.urlPC != null) {
      try {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Descargando imagen...")));
        final directory = await getApplicationDocumentsDirectory();
        final String filePath = path.join(directory.path, widget.serverImageName!);
        var response = await http.get(Uri.parse("http://${widget.urlPC}/api/foto/${widget.serverImageName}"));
        if (response.statusCode == 200) {
          File file = File(filePath);
          await file.writeAsBytes(response.bodyBytes);
          setState(() => _imagePath = filePath);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Error descargando imagen")));
        }
      } catch (e) {
        print(e);
      }
    }
  }

  Future<void> _openEditor() async {
    if (_imagePath == null) return;
    final bool? ok = await Navigator.push(context, MaterialPageRoute(builder: (_) => ImageEditorScreen(imageFile: File(_imagePath!))));
    if (ok == true) {
      setState(() { PaintingBinding.instance.imageCache.clear(); PaintingBinding.instance.imageCache.clearLiveImages(); });
    }
  }

  void _borrarFoto() => setState(() => _imagePath = null);

  void _guardarLocal(bool esTerminar) {
    if (_titleCtrl.text.isEmpty && !widget.esHistorial) return; // En historial el título puede estar vacío o ser fecha
    List<String> l = [];
    if (_isUrgente) l.add("Urgente");
    if (_isElectrico) l.add("Eléctrico");
    if (_isMecanico) l.add("Mecánico");
    if (_isPreventivo) l.add("Preventivo");
    if (_tagCtrl.text.isNotEmpty) l.add(_tagCtrl.text.trim());

    String detallesFinales = _descCtrl.text;

    // Si estamos editando un Pendiente PC, mantenemos la REF si existía
    if (widget.pendientePC != null) {
      final match = RegExp(r"\[REF:(\d+)\]").firstMatch(widget.pendientePC!.detalles);
      if (match != null) detallesFinales += " ${match.group(0)}";
    }

    Registro r = Registro(
      id: widget.registroExistente?.id,
      titulo: _titleCtrl.text,
      detalles: detallesFinales,
      tags: l.join(", "),
      imagePath: _imagePath);

    if (esTerminar) { widget.onSave(r); } else if (widget.onUpdate != null) { widget.onUpdate!(r); } else { widget.onSave(r); }
    if (widget.onUpdate == null || esTerminar) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    bool esTrabajoPC = widget.pendientePC != null;
    return Scaffold(
      appBar: AppBar(title: Text(widget.esHistorial ? "Editar Histórico" : (esTrabajoPC ? "Gestionar Trabajo" : "Nuevo")), backgroundColor: Colors.blueGrey),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          if (!widget.esHistorial) // Ocultar título en historial si se desea, o dejarlo
            TextField(controller: _titleCtrl, decoration: const InputDecoration(labelText: "Título")),
            const SizedBox(height: 15),
            TextField(controller: _descCtrl, maxLines: 5, decoration: const InputDecoration(labelText: "Detalles")),
            const SizedBox(height: 15),
            const Align(alignment: Alignment.centerLeft, child: Text("Etiquetas:", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey))),
            Wrap(
              spacing: 8.0,
              children: [
                FilterChip(label: const Text('🚨 Urgente'), selected: _isUrgente, selectedColor: Colors.red.withOpacity(0.3), onSelected: (v) => setState(() => _isUrgente = v)),
                FilterChip(label: const Text('⚡ Eléctrico'), selected: _isElectrico, selectedColor: Colors.blue.withOpacity(0.3), onSelected: (v) => setState(() => _isElectrico = v)),
                FilterChip(label: const Text('⚙️ Mecánico'), selected: _isMecanico, selectedColor: Colors.orange.withOpacity(0.3), onSelected: (v) => setState(() => _isMecanico = v)),
                FilterChip(label: const Text('🛡️ Preventivo'), selected: _isPreventivo, selectedColor: Colors.green.withOpacity(0.3), onSelected: (v) => setState(() => _isPreventivo = v)),
              ],
            ),
            TextField(controller: _tagCtrl, decoration: const InputDecoration(labelText: "Otras etiquetas (opcional)", hintText: "Ej: Rodamiento, Limpieza...", isDense: true)),
            const SizedBox(height: 15),
            const Divider(),

            if (_imagePath != null) ...[
              SizedBox(height: 300, child: Image.file(File(_imagePath!), fit: BoxFit.contain)),
              const SizedBox(height: 10),
              Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                ElevatedButton.icon(icon: const Icon(Icons.edit), label: const Text("DIBUJAR"), onPressed: _openEditor),
                const SizedBox(width: 10),
                ElevatedButton.icon(icon: const Icon(Icons.delete), label: const Text("BORRAR"), style: ElevatedButton.styleFrom(backgroundColor: Colors.red), onPressed: _borrarFoto),
              ])
            ] else ...[
              // Si no hay foto local, pero hay en server (Pendiente PC)
              if (widget.serverImageName != null && _imagePath == null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.cloud_download),
                    label: const Text("DESCARGAR FOTO ORIGINAL PARA EDITAR"),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
                    onPressed: _descargarParaVer,
                  ),
                ),

                ElevatedButton.icon(
                  icon: const Icon(Icons.camera_alt),
                  label: const Text("AÑADIR FOTO NUEVA"),
                  style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
                  onPressed: _takePhoto),
            ],

            const SizedBox(height: 20),

            if (esTrabajoPC) ...[
              Row(children: [
                Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.blue, padding: const EdgeInsets.symmetric(vertical: 15)), onPressed: () => _guardarLocal(false), child: const Text("ACTUALIZAR", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)))),
                const SizedBox(width: 10),
                Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: Colors.green, padding: const EdgeInsets.symmetric(vertical: 15)), onPressed: () => _guardarLocal(true), child: const Text("TERMINAR", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)))),
              ])
            ] else if (widget.esHistorial)
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: Colors.purple, minimumSize: const Size.fromHeight(50)),
              onPressed: () => _guardarLocal(true),
              child: const Text("GUARDAR CAMBIOS EN HISTÓRICO", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
            )
            else
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
  final _controller = ImagePainterController(color: Colors.red, strokeWidth: 4.0, mode: PaintMode.freeStyle);
  bool _guardando = false;
  @override
  void initState() { super.initState(); SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]); }
  @override
  void dispose() { SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp, DeviceOrientation.portraitDown, DeviceOrientation.landscapeLeft, DeviceOrientation.landscapeRight]); super.dispose(); }
  Future<void> _guardarImagen() async {
    if (_guardando) return;
    setState(() => _guardando = true);
    try {
      final bytes = await _controller.exportImage();
      if (bytes != null) { await widget.imageFile.writeAsBytes(bytes); if (mounted) Navigator.pop(context, true); }
    } catch (e) { ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error al guardar: $e"), backgroundColor: Colors.red)); } finally { if (mounted) setState(() => _guardando = false); }
  }
  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async => !_guardando,
      child: Scaffold(
        backgroundColor: Colors.grey[900],
        appBar: AppBar(
          backgroundColor: Colors.grey[900],
          iconTheme: const IconThemeData(color: Colors.white),
          title: Text(_guardando ? "Guardando..." : "Dibujar / Marcar", style: const TextStyle(color: Colors.white)),
          actions: [
            if (_guardando) const Padding(padding: EdgeInsets.all(16.0), child: SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.greenAccent)))
              else IconButton(icon: const Icon(Icons.check, color: Colors.greenAccent, size: 30), onPressed: _guardarImagen)
          ],
        ),
        body: _guardando ? const Center(child: CircularProgressIndicator(color: Colors.greenAccent)) : ImagePainter.file(widget.imageFile, controller: _controller, scalable: true),
      ),
    );
  }
}

// ==========================================
// 7. PESTAÑA AVISOS
// ==========================================
class TabAvisos extends StatefulWidget {
  const TabAvisos({super.key});
  @override
  State<TabAvisos> createState() => _TabAvisosState();
}

class _TabAvisosState extends State<TabAvisos> {
  List<AvisoPC> _avisos = [];

  // --- COLAS OFFLINE ---
  List<Map<String, String>> _colaCompletados = []; // Para poner en verde
  List<String> _colaRestaurar = [];                // Para poner en rojo (descompletar)

  bool _cargando = false;
  String? _urlPC;

  @override
  void initState() {
    super.initState();
    _inicializar();
  }

  Future<void> _inicializar() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() => _urlPC = prefs.getString('pc_ip_url'));

    // 1. Cargar Colas Offline
    String? colaComp = prefs.getString('avisos_cola_completados');
    if (colaComp != null) _colaCompletados = List<Map<String, String>>.from(json.decode(colaComp));

    String? colaRest = prefs.getString('avisos_cola_restaurar');
    if (colaRest != null) _colaRestaurar = List<String>.from(json.decode(colaRest));

    // 2. Cargar Datos Cacheados (Visualización inmediata)
    String? cache = prefs.getString('avisos_cache');
    if (cache != null) {
      try {
        final List<dynamic> data = json.decode(cache);
        setState(() => _avisos = data.map((x) => AvisoPC.fromJson(x)).toList());
      } catch (e) {}
    }

    // 3. Si hay red, sincronizamos
    if (_urlPC != null) _sincronizar();
  }

  Future<void> _guardarColas() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('avisos_cola_completados', json.encode(_colaCompletados));
    await prefs.setString('avisos_cola_restaurar', json.encode(_colaRestaurar));
  }

  Future<void> _sincronizar() async {
    if (_urlPC == null) return;
    if (!mounted) return;
    setState(() => _cargando = true);

    // PASO A: Procesar RESTAURACIONES (Desmarcar en servidor)
    List<String> restauradosOk = [];
    for (var id in _colaRestaurar) {
      try {
        final res = await http.post(
          Uri.parse("http://$_urlPC/api/descompletar_aviso"),
          body: {'id': id}
        ).timeout(const Duration(seconds: 5));

        if (res.statusCode == 200) restauradosOk.add(id);
      } catch (e) {
        print("Error restaurando: $e");
      }
    }

    // PASO B: Procesar COMPLETADOS (Marcar en servidor)
    List<Map<String, String>> completadosOk = [];
    for (var item in _colaCompletados) {
      try {
        final res = await http.post(
          Uri.parse("http://$_urlPC/api/completar_aviso"),
          body: {
            'id': item['id'],
            'titulo': item['titulo'],
            'fecha_custom': item['fecha']
          }
        ).timeout(const Duration(seconds: 5));

        if (res.statusCode == 200) completadosOk.add(item);
      } catch (e) {
        print("Error completando: $e");
      }
    }

    // Limpieza de colas locales
    if (restauradosOk.isNotEmpty || completadosOk.isNotEmpty) {
      setState(() {
        for (var id in restauradosOk) _colaRestaurar.remove(id);
        for (var item in completadosOk) _colaCompletados.remove(item);
      });
        await _guardarColas();
    }

    // PASO C: Descargar estado actualizado
    try {
      final res = await http.get(Uri.parse("http://$_urlPC/api/avisos")).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List<dynamic> data = json.decode(res.body);
        setState(() => _avisos = data.map((x) => AvisoPC.fromJson(x)).toList());

        // Actualizar caché
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('avisos_cache', res.body);
      }
    } catch (e) {
      // Si falla, seguimos con lo local
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  // --- ACCIÓN: COMPLETAR (Botón Verde) ---
  Future<void> _completarAviso(AvisoPC aviso) async {
    // Si el usuario le dio a "Desmarcar" offline y ahora se arrepiente,
    // simplemente quitamos la orden de desmarcar.
    if (_colaRestaurar.contains(aviso.id.toString())) {
      setState(() => _colaRestaurar.remove(aviso.id.toString()));
      await _guardarColas();
      return; // No hace falta sincronizar urgente, visualmente ya vuelve a ser verde
    }

    bool? confirmar = await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Confirmar"),
        content: Text("¿Marcar '${aviso.titulo}' como completado?"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("NO")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("SÍ", style: TextStyle(color: Colors.white))
          ),
        ],
      )
    );

    if (confirmar != true) return;

    final fechaHoy = DateTime.now().toString().split(' ')[0];

    // Añadir a cola de subida
    setState(() => _colaCompletados.add({
      'id': aviso.id.toString(),
      'titulo': aviso.titulo,
      'fecha': fechaHoy
    }));

    await _guardarColas();
    _sincronizar(); // Intentar subir ya
  }

  // --- ACCIÓN: DESMARCAR/DESHACER (Botón Rojo/Naranja) ---
  Future<void> _descompletarAviso(AvisoPC aviso) async {
    // Si estaba pendiente de subir (verde local), lo quitamos de la cola (Deshacer)
    if (_colaCompletados.any((item) => item['id'] == aviso.id.toString())) {
      setState(() {
        _colaCompletados.removeWhere((item) => item['id'] == aviso.id.toString());
      });
      await _guardarColas();
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("↩️ Acción deshecha")));
      return;
    }

    // Si ya era verde desde el servidor, pedimos confirmación para restaurar
    bool? confirmar = await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Desmarcar"),
        content: const Text("¿Volver a poner como PENDIENTE?\nSe borrará del historial."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("CANCELAR")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("DESMARCAR", style: TextStyle(color: Colors.white))
          ),
        ],
      )
    );

    if (confirmar != true) return;

    // Añadir a cola de restaurar
    setState(() => _colaRestaurar.add(aviso.id.toString()));
    await _guardarColas();
    _sincronizar(); // Intentar subir ya
  }

  Color _getColor(String code) {
    switch (code) {
      case 'red': return Colors.redAccent;
      case 'green': return Colors.green;
      case 'blue': return Colors.blue;
      default: return Colors.grey;
    }
  }

  IconData _getIcon(String code) {
    switch (code) {
      case 'red': return Icons.warning_amber_rounded;
      case 'green': return Icons.check_circle_outline;
      case 'blue': return Icons.calendar_month; // Icono para futuros
      default: return Icons.info_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_urlPC == null && _avisos.isEmpty) return const Center(child: Text("Conecta el PC para sincronizar"));

    int totalPendientes = _colaCompletados.length + _colaRestaurar.length;

    return Scaffold(
      body: Column(
        children: [
          // Barra Naranja de "Pendiente de Subir"
          if (totalPendientes > 0)
            Container(
              width: double.infinity,
              color: Colors.orangeAccent,
              padding: const EdgeInsets.all(8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.cloud_upload, color: Colors.white, size: 16),
                  const SizedBox(width: 8),
                  Text("$totalPendientes cambios pendientes", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                ],
              ),
            ),

            Expanded(
              child: _avisos.isEmpty
              ? const Center(child: Text("No hay avisos"))
              : RefreshIndicator(
                onRefresh: _sincronizar,
                child: ListView.builder(
                  padding: const EdgeInsets.all(10),
                  itemCount: _avisos.length,
                  itemBuilder: (ctx, i) {
                    final a = _avisos[i];
                    String idStr = a.id.toString();

                    // --- CALCULAR ESTADO VISUAL (Offline First) ---
                    bool enColaCompletar = _colaCompletados.any((item) => item['id'] == idStr);
                    bool enColaRestaurar = _colaRestaurar.contains(idStr);

                    String estadoVisual = a.estado;
                    String colorVisual = a.color;

                    if (enColaCompletar) {
                      estadoVisual = "LISTO (Subir)";
                      colorVisual = "green";
                    } else if (enColaRestaurar) {
                      estadoVisual = "PENDIENTE (Subir)";
                      colorVisual = "red";
                    }

                    // --- SELECCIÓN DE BOTÓN SEGÚN COLOR ---
                    Widget actionWidget;

                    if (colorVisual == 'green') {
                      // CASO 1: VERDE (Completado) -> Opción Desmarcar
                      actionWidget = ActionChip(
                        avatar: enColaCompletar
                        ? const Icon(Icons.undo, size: 14, color: Colors.white)
                        : const Icon(Icons.close, size: 14, color: Colors.white),
                        label: Text(enColaCompletar ? "Deshacer" : "Desmarcar",
                                    style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                                    backgroundColor: _getColor(colorVisual),
                                    onPressed: () => _descompletarAviso(a),
                                    padding: EdgeInsets.zero,
                                    visualDensity: VisualDensity.compact,
                      );
                    }
                    else if (colorVisual == 'red') {
                      // CASO 2: ROJO (Pendiente y Vencido) -> Opción Completar
                      actionWidget = ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                            visualDensity: VisualDensity.compact
                        ),
                        icon: const Icon(Icons.check, size: 16),
                        label: const Text("Completar"),
                        onPressed: () => _completarAviso(a),
                      );
                    }
                    else {
                      // CASO 3: AZUL (Futuro) -> Solo Información (Sin botón)
                      actionWidget = Chip(
                        label: Text(estadoVisual,
                                    style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                                    backgroundColor: _getColor(colorVisual),
                                    visualDensity: VisualDensity.compact,
                                    padding: EdgeInsets.zero,
                      );
                    }

                    return Card(
                      elevation: 2,
                      margin: const EdgeInsets.symmetric(vertical: 6),
                      shape: RoundedRectangleBorder(
                        side: BorderSide(color: _getColor(colorVisual).withOpacity(0.3), width: 1),
                        borderRadius: BorderRadius.circular(8)
                      ),
                      child: ListTile(
                        leading: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: _getColor(colorVisual).withOpacity(0.1),
                            shape: BoxShape.circle
                          ),
                          child: Icon(_getIcon(colorVisual), color: _getColor(colorVisual), size: 24)
                        ),
                        title: Text(a.titulo, style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text("Próxima: ${a.rango}", style: const TextStyle(fontSize: 12)),
                        trailing: actionWidget,
                      ),
                    );
                  },
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        mini: true,
        child: _cargando
        ? const Padding(padding: EdgeInsets.all(10), child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
        : Icon(Icons.sync, color: totalPendientes > 0 ? Colors.orange : Colors.white),
        backgroundColor: totalPendientes > 0 ? Colors.white : Colors.blue,
        onPressed: _sincronizar,
      ),
    );
  }
}
