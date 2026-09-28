// lib/features/services/providers/services_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api_client.dart';

// Modelo de lectura del catálogo
class ServiceItem {
  final String id;
  final String name;
  final double price;
  final int durationMinutes;
  final bool isActive;

  ServiceItem({
    required this.id,
    required this.name,
    required this.price,
    required this.durationMinutes,
    this.isActive = true,
  });

  factory ServiceItem.fromJson(Map<String, dynamic> json) {
    return ServiceItem(
      id: json['id'].toString(),
      name: (json['name'] ?? '').toString(),
      // Pydantic serializa `Decimal` como STRING ("1500.00"), no como number.
      // tryParse cubre ambos casos y no lanza, a diferencia de double.parse.
      price: double.tryParse(json['price'].toString()) ?? 0,
      durationMinutes: int.tryParse(json['duration_minutes'].toString()) ?? 30,
      isActive: json['is_active'] != false,
    );
  }
}

/// Catálogo completo, incluidos los servicios desactivados.
/// Lo consume la pantalla de administración.
final servicesListProvider = FutureProvider<List<ServiceItem>>((ref) async {
  final api = ref.watch(apiClientProvider).client;
  final response = await api.get('/services/');
  final data = response.data as List<dynamic>;
  return data
      .map((json) => ServiceItem.fromJson(json as Map<String, dynamic>))
      .toList();
});

/// Solo los servicios reservables.
///
/// El backend rechaza con 404 los servicios inactivos, así que ofrecerlos en el
/// selector de agendamiento garantizaba un error al confirmar el turno.
final activeServicesProvider = Provider<AsyncValue<List<ServiceItem>>>((ref) {
  return ref
      .watch(servicesListProvider)
      .whenData((services) => services.where((s) => s.isActive).toList());
});
