// lib/core/api_client.dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart'; // Necesario para kIsWeb y defaultTargetPlatform
import '../features/auth/providers/auth_provider.dart';

String _getBaseUrl() {
  if (kIsWeb) return 'http://127.0.0.1:8000/api/v1';
  if (defaultTargetPlatform == TargetPlatform.android)
    return 'http://10.0.2.2:8000/api/v1';
  return 'http://127.0.0.1:8000/api/v1';
}

class ApiClient {
  final Dio _dio;
  final FlutterSecureStorage _storage;
  final Function()? onUnauthenticated;

  ApiClient({this.onUnauthenticated})
    : _dio = Dio(
        BaseOptions(
          baseUrl: _getBaseUrl(), // Resolvemos la IP dinámicamente
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
        ),
      ),
      _storage = const FlutterSecureStorage() {
    _initializeInterceptors();
  }
  // ... el resto queda igual ...

  Dio get client => _dio;

  void _initializeInterceptors() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Antes de enviar cualquier petición, inyectamos el JWT si existe
          final token = await _storage.read(key: 'access_token');
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (DioException e, handler) {
          // Si el backend responde 401, ejecutamos la función de cierre de sesión
          if (e.response?.statusCode == 401) {
            onUnauthenticated?.call();
          }
          return handler.next(e);
        },
      ),
    );
  }
}

// Actualizamos el Provider para inyectar la función de logout
final apiClientProvider = Provider((ref) {
  return ApiClient(
    onUnauthenticated: () {
      // Forzamos el estado a desautenticado. GoRouter hará el resto.
      ref.read(authProvider.notifier).logout();
    },
  );
});
