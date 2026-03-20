/// Utilidades de diseño responsivo.
///
/// Breakpoints:
///   mobile  < 600px
///   tablet  >= 600px
///   desktop >= 1024px
library;

import 'package:flutter/material.dart';

class Breakpoints {
  static const double tablet = 600;
  static const double desktop = 1024;

  /// Máximo ancho del contenido principal en pantallas anchas.
  static const double maxContentWidth = 720;

  /// Máximo ancho de formularios (login, register, wizard).
  static const double maxFormWidth = 480;

  static bool isTablet(BuildContext context) =>
      MediaQuery.sizeOf(context).width >= tablet;

  static bool isDesktop(BuildContext context) =>
      MediaQuery.sizeOf(context).width >= desktop;

  static double contentPadding(BuildContext context) =>
      isTablet(context) ? 32 : 16;
}

/// Envuelve el contenido con ancho máximo centrado — útil en tablets.
///
/// [maxWidth] por defecto usa [Breakpoints.maxContentWidth].
/// [formLayout] usa [Breakpoints.maxFormWidth] para pantallas de formulario.
class ResponsiveCenter extends StatelessWidget {
  const ResponsiveCenter({
    super.key,
    required this.child,
    this.maxWidth,
    this.formLayout = false,
    this.padding,
  });

  final Widget child;
  final double? maxWidth;
  final bool formLayout;
  final EdgeInsetsGeometry? padding;

  @override
  Widget build(BuildContext context) {
    final width = maxWidth ??
        (formLayout
            ? Breakpoints.maxFormWidth
            : Breakpoints.maxContentWidth);

    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: width),
        child: padding != null ? Padding(padding: padding!, child: child) : child,
      ),
    );
  }
}

/// Wrapper responsivo para el body de un Scaffold.
///
/// En tablets centra el contenido con un ancho máximo.
/// Equivalente a poner un SafeArea + ResponsiveCenter dentro del body.
class ResponsiveBody extends StatelessWidget {
  const ResponsiveBody({
    super.key,
    required this.child,
    this.maxWidth,
    this.formLayout = false,
  });

  final Widget child;
  final double? maxWidth;
  final bool formLayout;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: BoxConstraints(
            maxWidth: maxWidth ??
                (formLayout
                    ? Breakpoints.maxFormWidth
                    : Breakpoints.maxContentWidth),
          ),
          child: child,
        ),
      ),
    );
  }
}
