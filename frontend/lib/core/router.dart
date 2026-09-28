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

/// Rutas accesibles sin sesión. Se evalúan ANTES que cualquier regla de auth.
const _publicRoutes = {'/public-booking'};

final routerProvider = Provider<GoRouter>((ref) {
  // El router se construye UNA sola vez. Antes se hacía
  // `final authState = ref.watch(authProvider)` y se devolvía un GoRouter
  // nuevo en cada cambio de sesión: eso resetea la navegación al
  // initialLocation y rompe los deep links. Ahora los cambios de auth se
  // propagan por refreshListenable.
  final refresh = ValueNotifier<AuthState>(ref.read(authProvider));
  ref.listen<AuthState>(authProvider, (_, next) => refresh.value = next);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/login',
    refreshListenable: refresh,
    redirect: (context, state) {
      final authState = ref.read(authProvider);
      final location = state.matchedLocation;

      // REGLA 0: las rutas públicas son accesibles SIEMPRE, en cualquier
      // estado de auth, incluso mientras se resuelve el storage. Si esto se
      // evalúa después de la regla de `initial`, un deep link o un QR a
      // /public-booking rebota a /loading y termina en el login del admin.
      if (_publicRoutes.contains(location)) return null;

      final isAuth = authState == AuthState.authenticated;

      // Todavía no sabemos si hay sesión: pantalla de espera.
      if (authState == AuthState.initial) {
        return location == '/loading' ? null : '/loading';
      }

      final isGoingToLogin = location == '/login';

      // Anónimo ya resuelto que quedó colgado en /loading -> Login.
      if (!isAuth && location == '/loading') return '/login';

      // REGLA 1 (Zero Trust): Anónimo en zona protegida -> Login
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
