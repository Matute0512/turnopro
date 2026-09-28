// lib/features/appointments/screens/dashboard_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../auth/providers/auth_provider.dart';
import '../providers/appointments_provider.dart';
import 'create_appointment_sheet.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Escuchamos el estado de la petición de turnos
    final appointmentsAsyncValue = ref.watch(appointmentsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Turnos Programados'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: () {
              // Esto actualiza el estado y GoRouter nos expulsa al Login
              ref.read(authProvider.notifier).logout();
            },
          ),
        ],
      ),
      // .when() garantiza que la UI responda a los 3 estados de la red
      body: appointmentsAsyncValue.when(
        data: (appointments) {
          if (appointments.isEmpty) {
            return const Center(child: Text('No hay turnos agendados.'));
          }

          return ListView.builder(
            itemCount: appointments.length,
            itemBuilder: (context, index) {
              final apt = appointments[index];
              // Formateamos la fecha usando el paquete intl
              final formattedTime = DateFormat(
                'dd/MM/yyyy HH:mm',
              ).format(apt.startTime);

              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: ListTile(
                  leading: const CircleAvatar(child: Icon(Icons.person)),
                  title: Text(
                    apt.customerFullName,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  subtitle: Text(
                    'Servicio ID: ${apt.serviceId} \nTel: ${apt.customerPhone}',
                  ),
                  trailing: Text(
                    formattedTime,
                    style: const TextStyle(
                      color: Colors.blue,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  isThreeLine: true,
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 48),
              const SizedBox(height: 16),
              Text('Error al cargar turnos: $error'),
              const SizedBox(height: 16),
              ElevatedButton(
                // Forzamos a Riverpod a reejecutar la petición HTTP
                onPressed: () => ref.invalidate(appointmentsProvider),
                child: const Text('Reintentar'),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          showModalBottomSheet(
            context: context,
            isScrollControlled:
                true, // Permite que el modal ocupe más altura si es necesario
            shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
            ),
            builder: (context) => const CreateAppointmentSheet(),
          );
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
