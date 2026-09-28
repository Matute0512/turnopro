// lib/features/services/providers/services_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api_client.dart';

// Modelo mínimo de lectura para el Dropdown
class ServiceItem {
  final String id;
  final String name;
  final double price;

  ServiceItem({required this.id, required this.name, required this.price});

  factory ServiceItem.fromJson(Map<String, dynamic> json) {
    return ServiceItem(
      id: json['id'].toString(),
      name: json['name'],
      price: json['price'].toDouble(),
    );
  }
}

// Proveedor que obtiene el catálogo desde FastAPI
final servicesListProvider = FutureProvider<List<ServiceItem>>((ref) async {
  final api = ref.watch(apiClientProvider).client;
  final response = await api.get('/services/');
  final List<dynamic> data = response.data;
  return data.map((json) => ServiceItem.fromJson(json)).toList();
});
