import 'package:flutter/material.dart';
import '../../../../core/api/app_config.dart';
import '../../../../core/api/mobikul_api_service.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/app_router.dart';

class SearchScreen extends StatefulWidget {
  final String? initialQuery;
  const SearchScreen({super.key, this.initialQuery});
  @override State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  late final TextEditingController _q;
  List _results = [];
  bool _loading = false;
  bool _searched = false;

  @override
  void initState() {
    super.initState();
    _q = TextEditingController(text: widget.initialQuery ?? '');
    if (widget.initialQuery != null && widget.initialQuery!.isNotEmpty) _search();
  }

  @override void dispose() { _q.dispose(); super.dispose(); }

  Future<void> _search() async {
    if (_q.text.trim().isEmpty) return;
    setState(() { _loading = true; _searched = true; });
    try {
      final d = await MobikulApi.instance.searchProducts(keyword: _q.text.trim());
      setState(() { _results = (d['products'] as List?) ?? (d['productList'] as List?) ?? []; _loading = false; });
    } catch (e) { setState(() { _loading = false; }); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primary,
      appBar: AppBar(
        title: TextField(
          controller: _q,
          autofocus: true,
          style: const TextStyle(color: Colors.white),
          cursorColor: AppTheme.accent,
          decoration: const InputDecoration(
            hintText: 'Search products...', hintStyle: TextStyle(color: AppTheme.textSecond),
            border: InputBorder.none, filled: false,
          ),
          onSubmitted: (_) => _search(),
        ),
        actions: [
          IconButton(icon: const Icon(Icons.search), onPressed: _search),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.accent))
          : !_searched
              ? const Center(child: Text('Search for products', style: TextStyle(color: AppTheme.textSecond)))
              : _results.isEmpty
                  ? const Center(child: Text('No results found', style: TextStyle(color: AppTheme.textSecond)))
                  : GridView.builder(
                      padding: const EdgeInsets.all(12),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2, childAspectRatio: 0.72, crossAxisSpacing: 10, mainAxisSpacing: 10,
                      ),
                      itemCount: _results.length,
                      itemBuilder: (ctx, i) => _card(_results[i]),
                    ),
    );
  }

  Widget _card(Map p) {
    final id  = p['id'] ?? p['template_id'] ?? 0;
    final img = p['image'] ?? '';
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, AppRouter.productDetail, arguments: id is int ? id : int.tryParse('$id') ?? 0),
      child: Container(
        decoration: BoxDecoration(color: AppTheme.surface, borderRadius: BorderRadius.circular(16)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            child: img.isNotEmpty
                ? Image.network(AppConfig.imageUrl(img), fit: BoxFit.cover, width: double.infinity,
                    errorBuilder: (_, __, ___) => Container(color: AppTheme.cardBg, child: const Icon(Icons.image_not_supported, color: AppTheme.textSecond)))
                : Container(color: AppTheme.cardBg, child: const Icon(Icons.shopping_bag_outlined, color: AppTheme.accent, size: 40)),
          )),
          Padding(padding: const EdgeInsets.all(10), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(p['name'] ?? '', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary), maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Text(p['price'] != null ? 'Rs. ${p['price']}' : '', style: const TextStyle(fontSize: 13, color: AppTheme.accent, fontWeight: FontWeight.w700)),
          ])),
        ]),
      ),
    );
  }
}
