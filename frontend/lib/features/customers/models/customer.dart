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
      id: json['id'],
      fullName: json['full_name'],
      phone: json['phone'],
      email: json['email'],
    );
  }
}
