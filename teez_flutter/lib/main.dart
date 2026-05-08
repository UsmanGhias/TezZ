import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'core/utils/app_router.dart';

void main() => runApp(const TezZApp());

class TezZApp extends StatelessWidget {
  const TezZApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TeZz',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      initialRoute: AppRouter.splash,
      onGenerateRoute: AppRouter.generateRoute,
    );
  }
}
