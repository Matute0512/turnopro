// lib/features/services/screens/services_admin_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../providers/services_provider.dart';
import '../../../core/api_client.dart';

class ServicesAdminScreen extends ConsumerStatefulWidget {
  const ServicesAdminScreen({super.key});

  @override
  ConsumerState<ServicesAdminScreen> createState() =>
      _ServicesAdminScreenState();
}

class _ServicesAdminScreenState extends ConsumerState<ServicesAdminScreen> {
  Future<void> _showServiceDialog([ServiceItem? service]) async {
    final formKey = GlobalKey<FormState>();
    final nameCtrl = TextEditingController(text: service?.name);
    final priceCtrl = TextEditingController(text: service?.price.toString());

    // Asumimos un default de 30 mins si no se lee.
    // Para simplificar MVP, duration_minutes se pide acá si es nuevo.
    final durationCtrl = TextEditingController(text: '30');

    bool isLoading = false;

    await showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          return AlertDialog(
            title: Text(service == null ? 'Nuevo Servicio' : 'Editar Servicio'),
            content: Form(
              key: formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextFormField(
                    controller: nameCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Nombre del Servicio',
                    ),
                    validator: (v) => v!.isEmpty ? 'Requerido' : null,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: priceCtrl,
                    decoration: const InputDecoration(labelText: 'Precio (\$)'),
                    keyboardType: TextInputType.number,
                    validator: (v) => v!.isEmpty ? 'Requerido' : null,
                  ),
                  if (service == null) ...[
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: durationCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Duración (minutos)',
                      ),
                      keyboardType: TextInputType.number,
                      validator: (v) => v!.isEmpty ? 'Requerido' : null,
                    ),
                  ],
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: isLoading ? null : () => Navigator.pop(context),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: isLoading
                    ? null
                    : () async {
                        if (!formKey.currentState!.validate()) return;

                        // double.parse/int.parse lanzan FormatException, que NO
                        // es una DioException: se escapaba del catch de abajo,
                        // no mostraba SnackBar y dejaba la pantalla en rojo.
                        // Se normaliza la coma decimal (entrada es-AR).
                        final price = double.tryParse(
                          priceCtrl.text.trim().replaceAll(',', '.'),
                        );
                        final duration = int.tryParse(durationCtrl.text.trim());

                        // Se capturan ANTES del await: este `context` es el del
                        // StatefulBuilder del diálogo, no el del State, así que
                        // el `mounted` del State no lo protege.
                        final messenger = ScaffoldMessenger.of(context);
                        final navigator = Navigator.of(context);

                        if (price == null ||
                            (service == null &&
                                (duration == null || duration <= 0))) {
                          messenger.showSnackBar(
                            const SnackBar(
                              content: Text('Precio o duración inválidos.'),
                            ),
                          );
                          setState(() => isLoading = false);
                          return;
                        }

                        setState(() => isLoading = true);
                        // Si el diálogo se cierra, su StatefulBuilder queda
                        // desmontado: resetear isLoading tiraría
                        // "setState() called after dispose()".
                        var closed = false;
                        try {
                          final api = ref.read(apiClientProvider).client;
                          if (service == null) {
                            await api.post(
                              '/services/',
                              data: {
                                'name': nameCtrl.text.trim(),
                                'price': price,
                                'duration_minutes': duration,
                              },
                            );
                          } else {
                            await api.put(
                              '/services/${service.id}',
                              data: {
                                'name': nameCtrl.text.trim(),
                                'price': price,
                              },
                            );
                          }
                          ref.invalidate(servicesListProvider);
                          navigator.pop();
                          closed = true;
                        } catch (e) {
                          // catch amplio a propósito: ya no puede haber
                          // FormatException acá, y un fallo de red debe verse
                          // igual que un error de validación del backend.
                          final message = e is DioException
                              ? '${e.response?.data ?? e.message}'
                              : '$e';
                          messenger.showSnackBar(
                            SnackBar(content: Text('Error: $message')),
                          );
                        } finally {
                          if (!closed) setState(() => isLoading = false);
                        }
                      },
                child: isLoading
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text('Guardar'),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _deleteService(String id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('¿Eliminar servicio?'),
        content: const Text('Esta acción no se puede deshacer.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    try {
      final api = ref.read(apiClientProvider).client;
      await api.delete('/services/$id');
      ref.invalidate(servicesListProvider);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final servicesAsync = ref.watch(servicesListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Gestor de Servicios')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showServiceDialog(),
        icon: const Icon(Icons.add),
        label: const Text('Nuevo Servicio'),
      ),
      body: servicesAsync.when(
        data: (services) {
          if (services.isEmpty) {
            return const Center(
              child: Text('No hay servicios. Crea uno nuevo.'),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: services.length,
            itemBuilder: (context, index) {
              final s = services[index];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  leading: const CircleAvatar(child: Icon(Icons.spa)),
                  title: Text(
                    s.name,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  subtitle: Text('\$${s.price.toStringAsFixed(2)}'),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: () => _showServiceDialog(s),
                      ),
                      IconButton(
                        icon: Icon(
                          Icons.delete_outline,
                          color: Theme.of(context).colorScheme.error,
                        ),
                        onPressed: () => _deleteService(s.id),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Error: $e')),
      ),
    );
  }
}
