import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class TezzLogo extends StatelessWidget {
  final double size;
  final bool showTagline;
  const TezzLogo({super.key, this.size = 60, this.showTagline = false});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppTheme.accent, AppTheme.gold],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(size * 0.22),
            boxShadow: [
              BoxShadow(
                color: AppTheme.accent.withOpacity(0.5),
                blurRadius: 20,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Center(
            child: Text(
              'Tz',
              style: TextStyle(
                fontSize: size * 0.42,
                fontWeight: FontWeight.w900,
                color: Colors.white,
                letterSpacing: -1,
              ),
            ),
          ),
        ),
        if (showTagline) ...[
          const SizedBox(height: 10),
          RichText(
            text: const TextSpan(
              children: [
                TextSpan(text: 'Te', style: TextStyle(color: AppTheme.textPrimary, fontSize: 28, fontWeight: FontWeight.w800)),
                TextSpan(text: 'Zz', style: TextStyle(color: AppTheme.accent, fontSize: 28, fontWeight: FontWeight.w900)),
              ],
            ),
          ),
          const Text('Shop Bold. Ship Fast.', style: TextStyle(color: AppTheme.textSecond, fontSize: 12, letterSpacing: 1)),
        ],
      ],
    );
  }
}
