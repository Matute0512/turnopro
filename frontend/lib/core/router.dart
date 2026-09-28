// lib/core/router.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../features/auth/providers/auth_provider.dart';
import '../features/auth/screens/login_screen.dart';
import '../features/appointments/screens/dashboard_screen.dart';
import '../features/customers/screens/customers_screen.dart';
import '../features/services/screens/services_admin_screen.dart';
import '../features/appointments/screens/public_booking_screen.dart';
import '../shared/widgets/responsive_layout.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/login',
    redirect: (context, state) {
      if (authState == AuthState.initial) return '/loading';

      final isAuth = authState == AuthState.authenticated;
      final isGoingToLogin = state.matchedLocation == '/login';
      final isPublic = state.matchedLocation == '/public-booking';

      // Portal publico sin proteccion
      if (isPublic) return null;

      // REGLA 1 (Zero Trust): Anónimo intentando acceder a zona protegida -> Login
      if (!isAuth && !isGoingToLogin) return '/login';

      // REGLA 2 (UX): Usuario logueado intentando ir al Login -> Dashboard
      if (isAuth && isGoingToLogin) return '/';

      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(
        path: '/public-booking',
        builder: (context, state) => const PublicBookingScreen(),
      ),
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
          GoRoute(
            path: '/clientes',
            builder: (context, state) => const CustomersScreen(),
          ),
          GoRoute(
            path: '/servicios',
            builder: (context, state) => const ServicesAdminScreen(),
          ),
        ],
      ),
    ],
  );
});
