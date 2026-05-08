import 'package:flutter/material.dart';
import '../../../../core/api/mobikul_api_service.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/app_router.dart';

class OrdersScreen extends StatefulWidget {
  const OrdersScreen({super.key});
  @override State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> {
  List _orders = [];
  bool _loading = true;
  String? _error;

  @override void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final d = await MobikulApi.instance.myOrders();
      setState(() { _orders = (d['orders'] as List?) ?? []; _loading = false; });
    } catch (e) { setState(() { _error = e.toString(); _loading = false; }); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primary,
      appBar: AppBar(title: const Text('My Orders')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.accent))
          : _error != null
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(_error!, style: const TextStyle(color: AppTheme.textSecond)),
                  const SizedBox(height: 16),
                  ElevatedButton(onPressed: _load, child: const Text('Retry')),
                ]))
              : _orders.isEmpty
                  ? const Center(child: Text('No orders yet', style: TextStyle(color: AppTheme.textSecond, fontSize: 16)))
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _orders.length,
                        itemBuilder: (ctx, i) => _orderCard(_orders[i]),
                      ),
                    ),
    );
  }

  Widget _orderCard(Map o) => Card(
    margin: const EdgeInsets.only(bottom: 12),
    child: ListTile(
      contentPadding: const EdgeInsets.all(14),
      title: Text('Order #${o['name'] ?? o['id']}', style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w700)),
      subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const SizedBox(height: 4),
        Text('Date: ${o['date_order'] ?? o['dateOrder'] ?? ''}', style: const TextStyle(color: AppTheme.textSecond, fontSize: 12)),
        const SizedBox(height: 2),
        Text('Total: Rs. ${o['amount_total'] ?? o['amountTotal'] ?? 0}', style: const TextStyle(color: AppTheme.accent, fontSize: 13, fontWeight: FontWeight.w600)),
      ]),
      trailing: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: AppTheme.success.withOpacity(0.2),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppTheme.success.withOpacity(0.5)),
        ),
        child: Text(o['state'] ?? o['status'] ?? 'done', style: const TextStyle(color: AppTheme.success, fontSize: 11)),
      ),
      onTap: () {
        final id = o['id'];
        if (id != null) Navigator.pushNamed(context, AppRouter.orderDetail, arguments: id is int ? id : int.parse('$id'));
      },
    ),
  );
}
