// lib/features/appointments/screens/create_appointment_sheet.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:intl/intl.dart';

import '../../../core/api_client.dart';
import '../providers/appointments_provider.dart';
import '../../services/providers/services_provider.dart';

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
  final _emailController = TextEditingController();

  String? _selectedServiceId;
  DateTime? _selectedDate;
  String? _selectedSlot;

  bool _isLoading = false;
  String? _errorMessage;

  List<String> _availableSlots = [];
  bool _isLoadingSlots = false;

  Future<void> _pickDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 90)),
    );
    if (date != null) {
      setState(() {
        _selectedDate = date;
        _selectedSlot = null;
      });
      _fetchAvailableSlots();
    }
  }

  void _onServiceChanged(String? val) {
    setState(() {
      _selectedServiceId = val;
      _selectedSlot = null;
    });
    _fetchAvailableSlots();
  }

  Future<void> _fetchAvailableSlots() async {
    if (_selectedDate == null || _selectedServiceId == null) return;

    setState(() {
      _isLoadingSlots = true;
      _errorMessage = null;
    });

    try {
      final api = ref.read(apiClientProvider).client;
      final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate!);
      final response = await api.get(
        '/appointments/available-slots',
        queryParameters: {'date': dateStr, 'service_id': _selectedServiceId},
      );

      setState(() {
        _availableSlots = List<String>.from(response.data);
      });
    } on DioException catch (e) {
      setState(() {
        _errorMessage =
            e.response?.data['detail'] ??
            'Error cargando horarios disponibles.';
        _availableSlots = [];
      });
    } finally {
      if (mounted) setState(() => _isLoadingSlots = false);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (_selectedDate == null ||
        _selectedSlot == null ||
        _selectedServiceId == null) {
      setState(() {
        _errorMessage = 'Por favor selecciona fecha, hora y servicio.';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final timeParts = _selectedSlot!.split(':');
      final startDateTime = DateTime(
        _selectedDate!.year,
        _selectedDate!.month,
        _selectedDate!.day,
        int.parse(timeParts[0]),
        int.parse(timeParts[1]),
      ).toUtc();

      final payload = {
        "customer_full_name": _nameController.text.trim(),
        "customer_phone": _phoneController.text.trim(),
        "customer_email": _emailController.text.trim().isEmpty
            ? null
            : _emailController.text.trim(),
        "service_id": _selectedServiceId,
        "start_time": startDateTime.toIso8601String(),
      };

      final api = ref.read(apiClientProvider).client;
      await api.post('/appointments/', data: payload);

      ref.invalidate(appointmentsProvider);

      if (mounted) Navigator.pop(context);
    } on DioException catch (e) {
      setState(() {
        final detail = e.response?.data?['detail'];
        if (detail is List) {
          _errorMessage = detail.map((err) => err['msg']).join(', ');
        } else {
          _errorMessage =
              detail?.toString() ?? 'Error de conexión o conflicto de turnos.';
        }
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  Widget _buildSlotsSelector() {
    if (_selectedDate == null || _selectedServiceId == null) {
      return const Text(
        'Selecciona un servicio y una fecha para ver horarios disponibles.',
        style: TextStyle(color: Colors.grey),
      );
    }

    if (_isLoadingSlots) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_availableSlots.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Text(
          'No hay horarios disponibles para esta fecha. Intenta con otro día.',
          textAlign: TextAlign.center,
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Horarios Disponibles',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8.0,
          runSpacing: 8.0,
          children: _availableSlots.map((slot) {
            final isSelected = _selectedSlot == slot;
            return ChoiceChip(
              label: Text(slot),
              selected: isSelected,
              showCheckmark: false,
              onSelected: (selected) {
                if (selected) setState(() => _selectedSlot = slot);
              },
            );
          }).toList(),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final servicesAsync = ref.watch(servicesListProvider);

    return Padding(
      // Padding dinámico para que el teclado no tape el formulario
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 24,
        right: 24,
        top: 16,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Indicador de arrastre (Drag handle)
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 24),
                  decoration: BoxDecoration(
                    color: Theme.of(
                      context,
                    ).colorScheme.onSurfaceVariant.withOpacity(0.4),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              Text(
                'Agendar Nuevo Turno',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 24),
              if (_errorMessage != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.errorContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.error_outline,
                        color: Theme.of(context).colorScheme.onErrorContainer,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style: TextStyle(
                            color: Theme.of(
                              context,
                            ).colorScheme.onErrorContainer,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

              TextFormField(
                controller: _nameController,
                decoration: InputDecoration(
                  labelText: 'Nombre Completo del Cliente',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  prefixIcon: const Icon(Icons.person_outline),
                ),
                validator: (v) => v!.isEmpty ? 'Requerido' : null,
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _phoneController,
                decoration: InputDecoration(
                  labelText: 'Teléfono',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  prefixIcon: const Icon(Icons.phone_outlined),
                ),
                keyboardType: TextInputType.phone,
                validator: (v) => v!.isEmpty ? 'Requerido' : null,
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _emailController,
                decoration: InputDecoration(
                  labelText: 'Correo Electrónico (Opcional)',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  prefixIcon: const Icon(Icons.email_outlined),
                ),
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 16),

              // Dropdown reactivo de Servicios
              servicesAsync.when(
                data: (services) => DropdownButtonFormField<String>(
                  decoration: InputDecoration(
                    labelText: 'Seleccionar Servicio',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    prefixIcon: const Icon(Icons.spa_outlined),
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
                  onChanged: _onServiceChanged,
                  validator: (v) => v == null ? 'Selecciona un servicio' : null,
                ),
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, st) => Text('Error cargando servicios: $e'),
              ),
              const SizedBox(height: 24),

              // Selector de Fecha (Botón ancho completo)
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                icon: const Icon(Icons.calendar_today),
                label: Text(
                  _selectedDate == null
                      ? 'Seleccionar Fecha'
                      : DateFormat('dd/MM/yyyy').format(_selectedDate!),
                ),
                onPressed: _pickDate,
              ),
              const SizedBox(height: 24),

              // Selector Dinámico Inteligente de Horas Disponibles
              _buildSlotsSelector(),

              const SizedBox(height: 32),

              FilledButton(
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onPressed: _isLoading ? null : _submit,
                child: _isLoading
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text(
                        'Confirmar Turno',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
