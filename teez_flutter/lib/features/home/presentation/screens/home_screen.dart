import 'package:flutter/material.dart';
import '../../../../core/api/app_config.dart';
import '../../../../core/api/mobikul_api_service.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/app_router.dart';
import '../../../../core/widgets/tezz_logo.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String? _error;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final d = await MobikulApi.instance.homepage();
      setState(() { _data = d; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primary,
      appBar: AppBar(
        title: const TezzLogo(size: 34),
        actions: [
          IconButton(icon: const Icon(Icons.search), onPressed: () => Navigator.pushNamed(context, AppRouter.search)),
          IconButton(icon: const Icon(Icons.favorite_outline), onPressed: () => Navigator.pushNamed(context, AppRouter.wishlist)),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.accent))
          : _error != null
              ? _errorWidget()
              : RefreshIndicator(onRefresh: _load, child: _body()),
    );
  }

  Widget _errorWidget() => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      const Icon(Icons.wifi_off_rounded, size: 60, color: AppTheme.textSecond),
      const SizedBox(height: 16),
      Text(_error ?? 'Failed to load', style: const TextStyle(color: AppTheme.textSecond), textAlign: TextAlign.center),
      const SizedBox(height: 20),
      ElevatedButton(onPressed: _load, child: const Text('Retry')),
    ]),
  );

  Widget _body() {
    final banners  = (_data?['banners']   as List?) ?? [];
    final products = (_data?['productSliderList'] as List?)?.expand((s) => (s['products'] as List?) ?? []).toList() ?? [];
    final cats     = (_data?['categories'] as List?) ?? [];

    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      children: [
        if (banners.isNotEmpty) _bannersSection(banners),
        if (cats.isNotEmpty) _categoriesSection(cats),
        _sectionTitle('Featured Products'),
        if (products.isEmpty)
          const Padding(
            padding: EdgeInsets.all(32),
            child: Center(child: Text('No products yet', style: TextStyle(color: AppTheme.textSecond))),
          )
        else
          _productsGrid(products),
      ],
    );
  }

  Widget _bannersSection(List banners) {
    return SizedBox(
      height: 180,
      child: PageView.builder(
        itemCount: banners.length,
        itemBuilder: (ctx, i) {
          final b = banners[i];
          final img = b['image_url'] ?? b['image'] ?? '';
          return Container(
            margin: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              gradient: const LinearGradient(colors: [AppTheme.surface, AppTheme.cardBg]),
            ),
            child: img.isNotEmpty
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.network(AppConfig.imageUrl(img), fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => const Icon(Icons.image_not_supported, color: AppTheme.textSecond, size: 48)),
                  )
                : const Center(child: Icon(Icons.photo, color: AppTheme.textSecond, size: 48)),
          );
        },
      ),
    );
  }

  Widget _categoriesSection(List cats) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      _sectionTitle('Categories'),
      SizedBox(
        height: 90,
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          itemCount: cats.length,
          itemBuilder: (ctx, i) {
            final c = cats[i];
            return GestureDetector(
              onTap: () => Navigator.pushNamed(context, AppRouter.search),
              child: Container(
                width: 70,
                margin: const EdgeInsets.only(right: 12),
                child: Column(
                  children: [
                    Container(
                      width: 52, height: 52,
                      decoration: BoxDecoration(
                        color: AppTheme.surface,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppTheme.accent.withOpacity(0.3)),
                      ),
                      child: const Icon(Icons.category_outlined, color: AppTheme.accent, size: 24),
                    ),
                    const SizedBox(height: 6),
                    Text(c['name'] ?? '', style: const TextStyle(fontSize: 10, color: AppTheme.textSecond), maxLines: 2, textAlign: TextAlign.center),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    ],
  );

  Widget _sectionTitle(String t) => Padding(
    padding: const EdgeInsets.fromLTRB(16, 20, 16, 10),
    child: Text(t, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
  );

  Widget _productsGrid(List products) => GridView.builder(
    shrinkWrap: true,
    physics: const NeverScrollableScrollPhysics(),
    padding: const EdgeInsets.symmetric(horizontal: 12),
    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
      crossAxisCount: 2, childAspectRatio: 0.72, crossAxisSpacing: 10, mainAxisSpacing: 10,
    ),
    itemCount: products.length > 20 ? 20 : products.length,
    itemBuilder: (ctx, i) => _productCard(products[i]),
  );

  Widget _productCard(Map p) {
    final id  = p['id'] ?? p['template_id'] ?? 0;
    final img = p['image'] ?? p['image_url'] ?? '';
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, AppRouter.productDetail, arguments: id is int ? id : int.tryParse('$id') ?? 0),
      child: Container(
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                child: img.isNotEmpty
                    ? Image.network(AppConfig.imageUrl(img), fit: BoxFit.cover, width: double.infinity,
                        errorBuilder: (_, __, ___) => Container(color: AppTheme.cardBg, child: const Icon(Icons.image_not_supported, color: AppTheme.textSecond)))
                    : Container(color: AppTheme.cardBg, child: const Icon(Icons.shopping_bag_outlined, color: AppTheme.accent, size: 40)),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(p['name'] ?? '', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary), maxLines: 2, overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 4),
                  Text(p['price'] != null ? 'Rs. ${p['price']}' : '', style: const TextStyle(fontSize: 13, color: AppTheme.accent, fontWeight: FontWeight.w700)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
