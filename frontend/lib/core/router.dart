// lib/core/router.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../features/auth/providers/auth_provider.dart';
import '../features/auth/screens/login_screen.dart';
import '../features/appointments/screens/dashboard_screen.dart';
import '../shared/widgets/responsive_layout.dart';

final routerProvider = Provider<GoRouter>((ref) {
  // Observamos el estado de autenticación reactivamente
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/login',
    // redirect actúa como middleware antes de cada navegación
    redirect: (context, state) {
      // Si la app está leyendo el secure storage, mostramos carga
      if (authState == AuthState.initial) return '/loading';

      final isAuth = authState == AuthState.authenticated;
      final isGoingToLogin = state.matchedLocation == '/login';

      // REGLA 1 (Zero Trust): Anónimo intentando acceder a zona protegida -> Rebote a Login
      if (!isAuth && !isGoingToLogin) return '/login';

      // REGLA 2 (UX): Usuario logueado intentando ir al Login -> Redirigir al Dashboard
      if (isAuth && isGoingToLogin) return '/';

      // REGLA 3: Todo en orden, deja continuar la navegación original
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(
        path: '/loading',
        builder: (context, state) =>
            const Scaffold(body: Center(child: CircularProgressIndicator())),
      ),
      ShellRoute(
        builder: (context, state, child) => ResponsiveLayout(child: child),
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => const DashboardScreen(),
          ),
        ],
      ),
    ],
  );
});
