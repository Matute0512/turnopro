// lib/features/customers/models/customer.dart
class Customer {
  final String id;
  final String fullName;
  final String phone;
  final String? email;

  Customer({
    required this.id,
    required this.fullName,
    required this.phone,
    this.email,
  });

  factory Customer.fromJson(Map<String, dynamic> json) {
    return Customer(
      // Casteo defensivo, consistente con Appointment y ServiceItem: un cambio
      // de tipo (o un null) del lado del backend no debe tumbar la pantalla con
      // un TypeError en runtime. La API devuelve el id como UUID -> String.
      id: json['id'].toString(),
      fullName: (json['full_name'] ?? 'Cliente sin nombre').toString(),
      phone: (json['phone'] ?? '').toString(),
      email: json['email'] as String?,
    );
  }
}
