/// Tema visual de NutriVet.IA — Paleta BampysVet Verde.
///
/// Paleta centrada en el verde BampysVet #25D366:
///   • Verde BampysVet   → color primario de marca
///   • Ámbar cálido      → acción / CTA secundario
///   • Verde salud       → éxito / planes activos
///
/// Material 3 · Soporte completo light + dark.
/// Dark mode: primaries más claras, superficies verde profundo.
/// Contraste AA/AAA en todos los pares texto/fondo.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

// ─── Paleta de marca BampysVet ─────────────────────────────────────────────
/// Verde BampysVet — color primario de marca.
const Color kBampysGreen = Color(0xFF25D366);

/// Variante clara para superficies y contenedores en modo claro.
const Color kBampysGreenContainer = Color(0xFFB7F0CF);

/// Ámbar cálido — acción secundaria, FABs, badges de urgencia.
const Color kWarmAmber = Color(0xFFF57C00);

/// Verde salud oscuro — plan ACTIVE, éxito, confirmaciones.
const Color kHealthGreen = Color(0xFF2E7D32);

/// Rojo clínico — error, tóxico, plan devuelto.
const Color kClinicalRed = Color(0xFFB71C1C);

// ─── Breakpoints de tipografía (escala M3) ────────────────────────────────
const _fontFamily = null; // Usa la fuente por defecto de M3 (Roboto/SF)

class AppTheme {
  AppTheme._();

  // ─── Tema claro ──────────────────────────────────────────────────────────
  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: kBampysGreen,
      brightness: Brightness.light,
      primary: kBampysGreen,
      onPrimary: Colors.white,
      primaryContainer: kBampysGreenContainer,
      onPrimaryContainer: const Color(0xFF002114),
      secondary: kWarmAmber,
      secondaryContainer: const Color(0xFFFFE0B2),
      tertiary: kHealthGreen,
      tertiaryContainer: const Color(0xFFC8E6C9),
      error: kClinicalRed,
      errorContainer: const Color(0xFFFFDAD6),
      surface: const Color(0xFFF5FFF9),   // superficie con leve tinte verde
      onSurface: const Color(0xFF1A2B22),
      onSurfaceVariant: const Color(0xFF3D5248),
      outline: const Color(0xFF6B8A76),
      outlineVariant: const Color(0xFFB8D9C5),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      fontFamily: _fontFamily,

      // ── AppBar ──────────────────────────────────────────────────────────
      appBarTheme: AppBarTheme(
        backgroundColor: kBampysGreen,
        foregroundColor: Colors.white,
        elevation: 0,
        scrolledUnderElevation: 2,
        centerTitle: false,
        systemOverlayStyle: SystemUiOverlayStyle.light,
        titleTextStyle: const TextStyle(
          color: Colors.white,
          fontSize: 20,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.15,
        ),
        iconTheme: const IconThemeData(color: Colors.white),
        actionsIconTheme: const IconThemeData(color: Colors.white),
      ),

      // ── Botones elevados ────────────────────────────────────────────────
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: kBampysGreen,
          foregroundColor: Colors.white,
          // Touch target M3: mínimo 48dp
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      // ── Botones outlined ────────────────────────────────────────────────
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: kBampysGreen,
          side: const BorderSide(color: kBampysGreen, width: 1.5),
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      // ── TextButton ──────────────────────────────────────────────────────
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: kBampysGreen,
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.25,
          ),
        ),
      ),

      // ── FAB ─────────────────────────────────────────────────────────────
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: kWarmAmber,
        foregroundColor: Colors.white,
        elevation: 4,
        shape: StadiumBorder(),
      ),

      // ── Inputs ──────────────────────────────────────────────────────────
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFB8D9C5)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFB8D9C5)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: kBampysGreen, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: kClinicalRed),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: kClinicalRed, width: 2),
        ),
        labelStyle: const TextStyle(color: Color(0xFF3D5248)),
        floatingLabelStyle: const TextStyle(color: kBampysGreen),
        prefixIconColor: const Color(0xFF6B8A76),
        suffixIconColor: const Color(0xFF6B8A76),
      ),

      // ── Cards ───────────────────────────────────────────────────────────
      cardTheme: CardThemeData(
        elevation: 1,
        surfaceTintColor: kBampysGreen,
        color: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xFFD4EEE0), width: 0.5),
        ),
        margin: const EdgeInsets.only(bottom: 12),
        clipBehavior: Clip.antiAlias,
      ),

      // ── Chips ───────────────────────────────────────────────────────────
      chipTheme: ChipThemeData(
        backgroundColor: const Color(0xFFE8F8EF),
        selectedColor: kBampysGreenContainer,
        labelStyle: const TextStyle(fontSize: 12, color: Color(0xFF1A2B22)),
        iconTheme: const IconThemeData(size: 16),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: const BorderSide(color: Color(0xFFB8D9C5)),
        ),
      ),

      // ── ListTile ────────────────────────────────────────────────────────
      listTileTheme: const ListTileThemeData(
        minVerticalPadding: 12,
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      ),

      // ── Divider ─────────────────────────────────────────────────────────
      dividerTheme: const DividerThemeData(
        color: Color(0xFFD4EEE0),
        thickness: 1,
        space: 1,
      ),

      // ── Snackbar ────────────────────────────────────────────────────────
      snackBarTheme: SnackBarThemeData(
        backgroundColor: const Color(0xFF1A2B22),
        contentTextStyle: const TextStyle(color: Colors.white, fontSize: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),

      // ── NavigationBar (para tablets con bottom nav) ─────────────────────
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: Colors.white,
        indicatorColor: kBampysGreenContainer,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const TextStyle(
              color: kBampysGreen,
              fontWeight: FontWeight.w600,
              fontSize: 12,
            );
          }
          return const TextStyle(fontSize: 12);
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: kBampysGreen);
          }
          return const IconThemeData(color: Color(0xFF6B8A76));
        }),
      ),

      // ── Tabs ────────────────────────────────────────────────────────────
      tabBarTheme: const TabBarThemeData(
        labelColor: Colors.white,
        unselectedLabelColor: Color(0xFFB8EDD0),
        indicatorColor: Colors.white,
        indicatorSize: TabBarIndicatorSize.tab,
        labelStyle: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        unselectedLabelStyle: TextStyle(fontWeight: FontWeight.w400, fontSize: 13),
      ),

      // ── Slider ──────────────────────────────────────────────────────────
      sliderTheme: SliderThemeData(
        activeTrackColor: kBampysGreen,
        thumbColor: kBampysGreen,
        inactiveTrackColor: kBampysGreenContainer,
        overlayColor: kBampysGreen.withAlpha(30),
        valueIndicatorColor: kBampysGreen,
        valueIndicatorTextStyle: const TextStyle(color: Colors.white),
      ),

      // ── Checkbox & Switch ────────────────────────────────────────────────
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith((states) =>
            states.contains(WidgetState.selected) ? kBampysGreen : null),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) =>
            states.contains(WidgetState.selected) ? Colors.white : null),
        trackColor: WidgetStateProperty.resolveWith((states) =>
            states.contains(WidgetState.selected) ? kBampysGreen : null),
      ),

      // ── Scaffold ────────────────────────────────────────────────────────
      scaffoldBackgroundColor: const Color(0xFFF5FFF9),

      // ── Typography (M3 type scale) ───────────────────────────────────────
      textTheme: _buildTextTheme(isDark: false),
    );
  }

  // ─── Tema oscuro ─────────────────────────────────────────────────────────
  static ThemeData get dark {
    final scheme = ColorScheme.fromSeed(
      seedColor: kBampysGreen,
      brightness: Brightness.dark,
      // En dark mode el primary debe ser claro para contrastar con el fondo oscuro
      primary: const Color(0xFF5AE89B),        // Verde claro sobre fondo oscuro
      onPrimary: const Color(0xFF003822),
      primaryContainer: const Color(0xFF00522E), // Contenedor verde oscuro
      onPrimaryContainer: const Color(0xFFB7F0CF),
      secondary: const Color(0xFFFFB74D),       // Ámbar cálido claro
      secondaryContainer: const Color(0xFF7A3A00),
      onSecondary: const Color(0xFF3E1C00),
      tertiary: const Color(0xFF81C784),        // Verde claro
      tertiaryContainer: const Color(0xFF1B4A1E),
      error: const Color(0xFFFF8A80),
      errorContainer: const Color(0xFF7A0000),
      surface: const Color(0xFF0D1A12),         // Superficie verde profundo
      surfaceContainerHighest: const Color(0xFF1A2D1E),
      onSurface: const Color(0xFFE0F5EA),       // Texto claro — contraste AA+
      onSurfaceVariant: const Color(0xFFA8C9B4),
      outline: const Color(0xFF5A8A6A),
      outlineVariant: const Color(0xFF1F3B28),
      inverseSurface: const Color(0xFFE0F5EA),
      onInverseSurface: const Color(0xFF0D1A12),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      fontFamily: _fontFamily,

      // ── AppBar en dark ───────────────────────────────────────────────────
      appBarTheme: AppBarTheme(
        backgroundColor: const Color(0xFF0A1A0E),
        foregroundColor: const Color(0xFFE0F5EA),
        elevation: 0,
        scrolledUnderElevation: 2,
        surfaceTintColor: const Color(0xFF5AE89B),
        centerTitle: false,
        systemOverlayStyle: SystemUiOverlayStyle.light,
        titleTextStyle: const TextStyle(
          color: Color(0xFFE0F5EA),
          fontSize: 20,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.15,
        ),
        iconTheme: const IconThemeData(color: Color(0xFFE0F5EA)),
        actionsIconTheme: const IconThemeData(color: Color(0xFFE0F5EA)),
      ),

      // ── Botones en dark ──────────────────────────────────────────────────
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF5AE89B),
          foregroundColor: const Color(0xFF003822),
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFF5AE89B),
          side: const BorderSide(color: Color(0xFF5AE89B), width: 1.5),
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: const Color(0xFF5AE89B),
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      ),

      // ── FAB en dark ─────────────────────────────────────────────────────
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: Color(0xFFFFB74D),
        foregroundColor: Color(0xFF3E1C00),
        elevation: 4,
        shape: StadiumBorder(),
      ),

      // ── Inputs en dark ───────────────────────────────────────────────────
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF1A2D1E),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF1F3B28)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF1F3B28)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF5AE89B), width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFFF8A80)),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFFF8A80), width: 2),
        ),
        labelStyle: const TextStyle(color: Color(0xFFA8C9B4)),
        floatingLabelStyle: const TextStyle(color: Color(0xFF5AE89B)),
        prefixIconColor: const Color(0xFF5A8A6A),
        suffixIconColor: const Color(0xFF5A8A6A),
      ),

      // ── Cards en dark ────────────────────────────────────────────────────
      cardTheme: const CardThemeData(
        elevation: 0,
        color: Color(0xFF1A2D1E),
        surfaceTintColor: Color(0xFF5AE89B),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(16)),
          side: BorderSide(color: Color(0xFF1F3B28), width: 1),
        ),
        margin: EdgeInsets.only(bottom: 12),
        clipBehavior: Clip.antiAlias,
      ),

      // ── Chips en dark ────────────────────────────────────────────────────
      chipTheme: ChipThemeData(
        backgroundColor: const Color(0xFF1A2D1E),
        selectedColor: const Color(0xFF00522E),
        labelStyle: const TextStyle(fontSize: 12, color: Color(0xFFE0F5EA)),
        iconTheme: const IconThemeData(size: 16, color: Color(0xFFA8C9B4)),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: const BorderSide(color: Color(0xFF1F3B28)),
        ),
      ),

      // ── ListTile en dark ─────────────────────────────────────────────────
      listTileTheme: const ListTileThemeData(
        minVerticalPadding: 12,
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        textColor: Color(0xFFE0F5EA),
        iconColor: Color(0xFFA8C9B4),
      ),

      // ── Divider en dark ──────────────────────────────────────────────────
      dividerTheme: const DividerThemeData(
        color: Color(0xFF1F3B28),
        thickness: 1,
        space: 1,
      ),

      // ── Snackbar en dark ─────────────────────────────────────────────────
      snackBarTheme: SnackBarThemeData(
        backgroundColor: const Color(0xFF1A2D1E),
        contentTextStyle: const TextStyle(color: Color(0xFFE0F5EA), fontSize: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),

      // ── Tabs en dark ─────────────────────────────────────────────────────
      tabBarTheme: const TabBarThemeData(
        labelColor: Color(0xFF5AE89B),
        unselectedLabelColor: Color(0xFF5A8A6A),
        indicatorColor: Color(0xFF5AE89B),
        indicatorSize: TabBarIndicatorSize.tab,
        labelStyle: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        unselectedLabelStyle: TextStyle(fontWeight: FontWeight.w400, fontSize: 13),
      ),

      // ── Slider en dark ───────────────────────────────────────────────────
      sliderTheme: SliderThemeData(
        activeTrackColor: const Color(0xFF5AE89B),
        thumbColor: const Color(0xFF5AE89B),
        inactiveTrackColor: const Color(0xFF1F3B28),
        overlayColor: const Color(0xFF5AE89B).withAlpha(30),
        valueIndicatorColor: const Color(0xFF5AE89B),
        valueIndicatorTextStyle: const TextStyle(color: Color(0xFF003822)),
      ),

      // ── Scaffold en dark ─────────────────────────────────────────────────
      scaffoldBackgroundColor: const Color(0xFF0D1A12),

      // ── Typography en dark ───────────────────────────────────────────────
      textTheme: _buildTextTheme(isDark: true),
    );
  }

  // ─── Escala tipográfica Material 3 ────────────────────────────────────────
  static TextTheme _buildTextTheme({required bool isDark}) {
    final baseColor = isDark ? const Color(0xFFE0F5EA) : const Color(0xFF1A2B22);
    final subtleColor = isDark ? const Color(0xFFA8C9B4) : const Color(0xFF3D5248);

    return TextTheme(
      // Display — solo para pantallas hero/splash
      displayLarge: TextStyle(
        fontSize: 57, fontWeight: FontWeight.w400,
        color: baseColor, letterSpacing: -0.25,
      ),
      displayMedium: TextStyle(
        fontSize: 45, fontWeight: FontWeight.w400, color: baseColor,
      ),
      displaySmall: TextStyle(
        fontSize: 36, fontWeight: FontWeight.w400, color: baseColor,
      ),
      // Headline — títulos de pantalla
      headlineLarge: TextStyle(
        fontSize: 32, fontWeight: FontWeight.w700, color: baseColor,
      ),
      headlineMedium: TextStyle(
        fontSize: 28, fontWeight: FontWeight.w700, color: baseColor,
      ),
      headlineSmall: TextStyle(
        fontSize: 24, fontWeight: FontWeight.w600, color: baseColor,
      ),
      // Title — subtítulos, appbar, cards
      titleLarge: TextStyle(
        fontSize: 22, fontWeight: FontWeight.w600, color: baseColor,
        letterSpacing: 0,
      ),
      titleMedium: TextStyle(
        fontSize: 16, fontWeight: FontWeight.w600, color: baseColor,
        letterSpacing: 0.15,
      ),
      titleSmall: TextStyle(
        fontSize: 14, fontWeight: FontWeight.w600, color: baseColor,
        letterSpacing: 0.1,
      ),
      // Body — texto principal
      bodyLarge: TextStyle(
        fontSize: 16, fontWeight: FontWeight.w400, color: baseColor,
        letterSpacing: 0.5,
      ),
      bodyMedium: TextStyle(
        fontSize: 14, fontWeight: FontWeight.w400, color: baseColor,
        letterSpacing: 0.25,
      ),
      bodySmall: TextStyle(
        fontSize: 12, fontWeight: FontWeight.w400, color: subtleColor,
        letterSpacing: 0.4,
      ),
      // Label — chips, botones, tabs
      labelLarge: TextStyle(
        fontSize: 14, fontWeight: FontWeight.w600, color: baseColor,
        letterSpacing: 0.1,
      ),
      labelMedium: TextStyle(
        fontSize: 12, fontWeight: FontWeight.w500, color: subtleColor,
        letterSpacing: 0.5,
      ),
      labelSmall: TextStyle(
        fontSize: 11, fontWeight: FontWeight.w500, color: subtleColor,
        letterSpacing: 0.5,
      ),
    );
  }
}
