import 'package:flutter/material.dart';

class UniversalCameraView extends StatelessWidget {
  final Widget Function(BuildContext) loadingBuilder;
  final Widget Function(BuildContext, String) errorBuilder;
  final VoidCallback onReady;

  const UniversalCameraView({
    super.key,
    required this.loadingBuilder,
    required this.errorBuilder,
    required this.onReady,
  });

  @override
  Widget build(BuildContext context) => loadingBuilder(context);
}
