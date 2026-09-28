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
    return Appointment(
      id: json['id'].toString(),
      // Absorción de nulos para prevenir el TypeError fatal
      customerFullName: json['customer_full_name'] ?? 'Cliente Desconocido',
      customerPhone: json['customer_phone'] ?? 'Sin Teléfono',
      startTime: DateTime.parse(json['start_time']).toLocal(),
      serviceId: json['service_id'].toString(),
    );
  }
}
