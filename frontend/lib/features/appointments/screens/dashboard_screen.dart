// lib/features/appointments/screens/dashboard_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:table_calendar/table_calendar.dart';

import '../../auth/providers/auth_provider.dart';
import '../providers/appointments_provider.dart';
import '../models/appointment.dart';
import 'create_appointment_sheet.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay = DateTime.now();

  @override
  Widget build(BuildContext context) {
    final appointmentsAsyncValue = ref.watch(appointmentsProvider);
    final isDesktop = MediaQuery.of(context).size.width >= 600;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Calendario de Turnos'),
        centerTitle: false,
        actions: [
          if (!isDesktop)
            IconButton(
              icon: const Icon(Icons.logout),
              tooltip: 'Cerrar sesión',
              onPressed: () {
                ref.read(authProvider.notifier).logout();
              },
            ),
        ],
      ),
      body: appointmentsAsyncValue.when(
        data: (allAppointments) {
          // Filtrar turnos del día seleccionado
          final selectedDayAppointments = allAppointments.where((apt) {
            return isSameDay(apt.startTime, _selectedDay);
          }).toList();

          // Ordenar por hora (cronológico)
          selectedDayAppointments.sort(
            (a, b) => a.startTime.compareTo(b.startTime),
          );

          return Column(
            children: [
              // 1. Calendario Visual Interactivo
              Container(
                color: Theme.of(context).colorScheme.surface,
                child: TableCalendar<Appointment>(
                  firstDay: DateTime.now().subtract(const Duration(days: 365)),
                  lastDay: DateTime.now().add(const Duration(days: 365)),
                  focusedDay: _focusedDay,
                  selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
                  onDaySelected: (selectedDay, focusedDay) {
                    setState(() {
                      _selectedDay = selectedDay;
                      _focusedDay = focusedDay;
                    });
                  },
                  calendarFormat: CalendarFormat
                      .week, // Formato por defecto para no tapar toda la pantalla
                  availableCalendarFormats: const {
                    CalendarFormat.week: 'Semana',
                    CalendarFormat.month: 'Mes',
                  },
                  // eventLoader es crucial para mostrar los puntitos de los turnos en los días
                  eventLoader: (day) {
                    return allAppointments
                        .where((apt) => isSameDay(apt.startTime, day))
                        .toList();
                  },
                  calendarStyle: CalendarStyle(
                    todayDecoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      shape: BoxShape.circle,
                    ),
                    todayTextStyle: TextStyle(
                      color: Theme.of(context).colorScheme.onPrimaryContainer,
                      fontWeight: FontWeight.bold,
                    ),
                    selectedDecoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primary,
                      shape: BoxShape.circle,
                    ),
                    markerDecoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.tertiary,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              ),
              const Divider(height: 1),

              // 2. Lista de Turnos del Día Seleccionado
              Expanded(
                child: selectedDayAppointments.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.event_available,
                              size: 64,
                              color: Theme.of(
                                context,
                              ).colorScheme.outlineVariant,
                            ),
                            const SizedBox(height: 16),
                            Text(
                              'Día libre. No hay turnos agendados.',
                              style: Theme.of(context).textTheme.titleMedium
                                  ?.copyWith(
                                    color: Theme.of(
                                      context,
                                    ).colorScheme.onSurfaceVariant,
                                  ),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        itemCount: selectedDayAppointments.length,
                        itemBuilder: (context, index) {
                          final apt = selectedDayAppointments[index];
                          final formattedTime = DateFormat(
                            'HH:mm',
                          ).format(apt.startTime);

                          return Padding(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 6,
                            ),
                            child: Card(
                              elevation: 0,
                              color: Theme.of(
                                context,
                              ).colorScheme.surfaceContainerHighest,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Padding(
                                padding: const EdgeInsets.all(8.0),
                                child: ListTile(
                                  leading: CircleAvatar(
                                    backgroundColor: Theme.of(
                                      context,
                                    ).colorScheme.primary,
                                    foregroundColor: Theme.of(
                                      context,
                                    ).colorScheme.onPrimary,
                                    child: Text(
                                      apt.customerFullName.isNotEmpty
                                          ? apt.customerFullName[0]
                                                .toUpperCase()
                                          : '?',
                                    ),
                                  ),
                                  title: Text(
                                    apt.customerFullName,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  subtitle: Padding(
                                    padding: const EdgeInsets.only(top: 4.0),
                                    child: Text('Tel: ${apt.customerPhone}'),
                                  ),
                                  trailing: Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 16,
                                      vertical: 8,
                                    ),
                                    decoration: BoxDecoration(
                                      color: Theme.of(
                                        context,
                                      ).colorScheme.primaryContainer,
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Text(
                                      formattedTime,
                                      style: TextStyle(
                                        color: Theme.of(
                                          context,
                                        ).colorScheme.onPrimaryContainer,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 16,
                                      ),
                                    ),
                                  ),
                                  isThreeLine: true,
                                ),
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                color: Theme.of(context).colorScheme.error,
                size: 48,
              ),
              const SizedBox(height: 16),
              Text('Error al cargar turnos: $error'),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: () => ref.invalidate(appointmentsProvider),
                icon: const Icon(Icons.refresh),
                label: const Text('Reintentar'),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: isDesktop
          ? FloatingActionButton.extended(
              onPressed: () => _showCreateSheet(context),
              icon: const Icon(Icons.add),
              label: const Text('Nuevo Turno'),
            )
          : FloatingActionButton(
              onPressed: () => _showCreateSheet(context),
              child: const Icon(Icons.add),
            ),
    );
  }

  void _showCreateSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => const CreateAppointmentSheet(),
    );
  }
}
