// lib/features/appointments/models/appointment.dart

class Appointment {
  final String id; // Cambiado de int a String para soportar UUIDs
  final String customerFullName;
  final String customerPhone;
  final DateTime startTime;
  final String serviceId; // Cambiado de int a String

  Appointment({
    required this.id,
    required this.customerFullName,
    required this.customerPhone,
    required this.startTime,
    required this.serviceId,
  });

  factory Appointment.fromJson(Map<String, dynamic> json) {
    final rawId = json['id'];
    final rawStart = json['start_time'];

    // Fallar temprano y con contexto. Antes, `json['id'].toString()` sobre un
    // null producía el string "null" en silencio, y un start_time nulo
    // reventaba en DateTime.parse() tres capas más arriba, lejos de la causa.
    if (rawId == null || rawStart == null) {
      throw FormatException(
        'Appointment malformado (falta id o start_time): $json',
      );
    }

    return Appointment(
      id: rawId.toString(),
      // Absorción de nulos para prevenir el TypeError fatal
      customerFullName: (json['customer_full_name'] ?? 'Cliente Desconocido')
          .toString(),
      customerPhone: (json['customer_phone'] ?? 'Sin Teléfono').toString(),
      // El backend manda ISO-8601 con offset explícito; toLocal() lo lleva a
      // la hora del equipo. Sin el offset, Dart lo interpretaría como local
      // y el turno aparecería corrido varias horas en el calendario.
      startTime: DateTime.parse(rawStart as String).toLocal(),
      serviceId: json['service_id'].toString(),
    );
  }
}
