// lib/features/appointments/providers/appointments_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api_client.dart';
import '../models/appointment.dart';

// Este provider hace la petición HTTP y devuelve la lista parseada
final appointmentsProvider = FutureProvider<List<Appointment>>((ref) async {
  // Obtenemos la instancia de Dio (que ya tiene el token inyectado)
  final api = ref.watch(apiClientProvider).client;

  // Asumiendo que tienes un endpoint GET /appointments/ en tu backends
  final response = await api.get('/appointments/');

  final List<dynamic> data = response.data;
  return data.map((json) => Appointment.fromJson(json)).toList();
});
