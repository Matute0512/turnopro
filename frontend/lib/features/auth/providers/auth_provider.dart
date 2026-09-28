import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

// 1. Los tres estados posibles de nuestra aplicación
enum AuthState { initial, authenticated, unauthenticated }

// 2. Inyección de la bóveda criptográfica
final secureStorageProvider = Provider((ref) => const FlutterSecureStorage());

// 3. Notificador moderno (Riverpod 2.x)
class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    // build() define el estado inicial. Lanzamos la verificación en segundo plano.
    _checkAuthStatus();
    return AuthState.initial;
  }

  Future<void> _checkAuthStatus() async {
    // Usamos ref.read() para acceder al storage directamente
    final storage = ref.read(secureStorageProvider);
    final token = await storage.read(key: 'access_token');

    if (token != null) {
      state = AuthState.authenticated;
    } else {
      state = AuthState.unauthenticated;
    }
  }

  Future<void> login(String token) async {
    final storage = ref.read(secureStorageProvider);
    await storage.write(key: 'access_token', value: token);
    state = AuthState.authenticated; // Esto dispara la redirección de GoRouter
  }

  Future<void> logout() async {
    final storage = ref.read(secureStorageProvider);
    await storage.delete(key: 'access_token');
    state = AuthState.unauthenticated;
  }
}

// 4. Provider moderno para nuestro AuthNotifier
final authProvider = NotifierProvider<AuthNotifier, AuthState>(() {
  return AuthNotifier();
});
