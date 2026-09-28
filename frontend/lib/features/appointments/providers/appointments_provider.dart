// lib/features/appointments/providers/appointments_provider.dart
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api_client.dart';
import '../models/appointment.dart';

// Este provider hace la petición HTTP y devuelve la lista parseada
final appointmentsProvider = FutureProvider<List<Appointment>>((ref) async {
  // Obtenemos la instancia de Dio (que ya tiene el token inyectado)
  final api = ref.watch(apiClientProvider).client;

  // El backend pagina con skip/limit y todavía no hay scroll infinito: si se
  // omite `limit`, el default de 100 trunca el calendario EN SILENCIO (los
  // días posteriores dejan de marcarse sin ningún error visible).
  // Cuando la agenda supere este tope, migrar a un filtro por rango de fechas
  // (?date_from=&date_to=) en vez de seguir subiendo el número.
  const pageSize = 500;
  final response = await api.get(
    '/appointments/',
    queryParameters: {'skip': 0, 'limit': pageSize},
  );

  final data = response.data as List<dynamic>;
  final items = data
      .map((json) => Appointment.fromJson(json as Map<String, dynamic>))
      .toList();

  if (items.length >= pageSize) {
    debugPrint(
      'ATENCION: se alcanzo el tope de $pageSize turnos; '
      'hay turnos sin mostrar en el calendario.',
    );
  }

  return items;
});
