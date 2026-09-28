// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/router.dart';

void main() {
  runApp(
    // ProviderScope intercepta y distribuye todas las dependencias
    const ProviderScope(child: TurnoProApp()),
  );
}

// Cambiamos StatelessWidget por ConsumerWidget para poder leer a Riverpod
class TurnoProApp extends ConsumerWidget {
  const TurnoProApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Escuchamos nuestro router configurado
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'TurnoPro',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.blue,
        brightness: Brightness.light,
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.blue,
        brightness: Brightness.dark,
      ),
      themeMode: ThemeMode.system,
      routerConfig: router,
    );
  }
}
