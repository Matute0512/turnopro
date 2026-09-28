// lib/features/customers/providers/customers_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api_client.dart';
import '../models/customer.dart';

final customersProvider = FutureProvider<List<Customer>>((ref) async {
  final api = ref.watch(apiClientProvider).client;
  final response = await api.get('/customers/');
  final List<dynamic> data = response.data;
  return data.map((json) => Customer.fromJson(json)).toList();
});
