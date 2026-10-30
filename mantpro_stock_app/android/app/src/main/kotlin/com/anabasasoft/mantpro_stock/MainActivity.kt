package com.anabasasoft.mantpro_stock

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.content.FileProvider
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File

/**
 * Además de la actividad de Flutter, instala las actualizaciones descargadas
 * desde la app (canal "mantpro/actualizador"): abre el instalador de Android
 * con el APK. Si la app aún no tiene permiso para instalar aplicaciones,
 * abre antes esa pantalla de ajustes y, al volver con el permiso concedido,
 * lanza la instalación sola.
 */
class MainActivity : FlutterActivity() {
    private var apkPendiente: File? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "mantpro/actualizador")
            .setMethodCallHandler { llamada, resultado ->
                if (llamada.method == "instalar") {
                    val ruta = llamada.argument<String>("ruta")
                    if (ruta == null) {
                        resultado.error("sin_ruta", "Falta la ruta del APK", null)
                    } else {
                        resultado.success(instalar(File(ruta)))
                    }
                } else {
                    resultado.notImplemented()
                }
            }
    }

    /** "instalando", o "permiso" si se ha abierto la pantalla de ajustes. */
    private fun instalar(apk: File): String {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && !packageManager.canRequestPackageInstalls()) {
            apkPendiente = apk
            startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:$packageName")))
            return "permiso"
        }
        val uri = FileProvider.getUriForFile(this, "$packageName.instalador", apk)
        startActivity(Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        })
        return "instalando"
    }

    override fun onResume() {
        super.onResume()
        // Vuelta de la pantalla de "Instalar aplicaciones desconocidas".
        val apk = apkPendiente ?: return
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O || packageManager.canRequestPackageInstalls()) {
            apkPendiente = null
            if (apk.exists()) instalar(apk)
        }
    }
}
