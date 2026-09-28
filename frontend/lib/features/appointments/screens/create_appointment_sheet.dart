// lib/features/appointments/screens/create_appointment_sheet.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:intl/intl.dart';

import '../../../core/api_client.dart';
import '../../services/providers/services_provider.dart';
import '../providers/appointments_provider.dart';

class CreateAppointmentSheet extends ConsumerStatefulWidget {
  const CreateAppointmentSheet({super.key});

  @override
  ConsumerState<CreateAppointmentSheet> createState() =>
      _CreateAppointmentSheetState();
}

class _CreateAppointmentSheetState
    extends ConsumerState<CreateAppointmentSheet> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();

  String? _selectedServiceId;
  DateTime? _selectedDate;
  TimeOfDay? _selectedTime;

  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _pickDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (date != null) setState(() => _selectedDate = date);
  }

  Future<void> _pickTime() async {
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (time != null) setState(() => _selectedTime = time);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedDate == null ||
        _selectedTime == null ||
        _selectedServiceId == null) {
      setState(() => _errorMessage = 'Por favor completa todos los campos.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // 1. Combinamos Date y Time y lo convertimos a formato UTC ISO 8601 para FastAPI
      final startDateTime = DateTime(
        _selectedDate!.year,
        _selectedDate!.month,
        _selectedDate!.day,
        _selectedTime!.hour,
        _selectedTime!.minute,
      ).toUtc();

      // 2. Preparamos el payload
      final payload = {
        "customer_full_name": _nameController.text.trim(),
        "customer_phone": _phoneController.text.trim(),
        "service_id": _selectedServiceId,
        "start_time": startDateTime.toIso8601String(),
      };

      // 3. Enviamos la petición
      final api = ref.read(apiClientProvider).client;
      await api.post('/appointments/', data: payload);

      // 4. ÉXITO: Forzamos la recarga del Dashboard y cerramos el modal
      ref.invalidate(appointmentsProvider);
      if (mounted) Navigator.of(context).pop();
    } on DioException catch (e) {
      setState(() {
        _errorMessage =
            e.response?.data['detail'] ??
            'Error de conexión o conflicto de turnos (Overbooking).';
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final servicesAsync = ref.watch(servicesListProvider);

    return Padding(
      // Padding dinámico para que el teclado no tape el formulario
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 16,
        right: 16,
        top: 24,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Agendar Nuevo Turno',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              if (_errorMessage != null)
                Container(
                  padding: const EdgeInsets.all(8),
                  color: Colors.red.shade100,
                  child: Text(
                    _errorMessage!,
                    style: TextStyle(color: Colors.red.shade900),
                  ),
                ),

              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Nombre Completo del Cliente',
                ),
                validator: (v) => v!.isEmpty ? 'Requerido' : null,
              ),
              const SizedBox(height: 8),

              TextFormField(
                controller: _phoneController,
                decoration: const InputDecoration(labelText: 'Teléfono'),
                keyboardType: TextInputType.phone,
                validator: (v) => v!.isEmpty ? 'Requerido' : null,
              ),
              const SizedBox(height: 16),

              // Dropdown reactivo de Servicios
              servicesAsync.when(
                data: (services) => DropdownButtonFormField<String>(
                  decoration: const InputDecoration(
                    labelText: 'Seleccionar Servicio',
                  ),
                  value: _selectedServiceId,
                  items: services
                      .map(
                        (s) => DropdownMenuItem(
                          value: s.id,
                          child: Text('${s.name} (\$${s.price})'),
                        ),
                      )
                      .toList(),
                  onChanged: (val) => setState(() => _selectedServiceId = val),
                  validator: (v) => v == null ? 'Selecciona un servicio' : null,
                ),
                loading: () => const CircularProgressIndicator(),
                error: (e, st) => Text('Error cargando servicios: $e'),
              ),
              const SizedBox(height: 16),

              // Selectores de Fecha y Hora
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.calendar_today),
                      label: Text(
                        _selectedDate == null
                            ? 'Fecha'
                            : DateFormat('dd/MM/yyyy').format(_selectedDate!),
                      ),
                      onPressed: _pickDate,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.access_time),
                      label: Text(
                        _selectedTime == null
                            ? 'Hora'
                            : _selectedTime!.format(context),
                      ),
                      onPressed: _pickTime,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                child: _isLoading
                    ? const CircularProgressIndicator()
                    : const Text('Confirmar Turno'),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
