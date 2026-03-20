/// Tema visual de NutriVet.IA — Paleta BampysVet Azul.
///
/// Paleta centrada en el azul royal BampysVet #1853C0:
///   • Azul royal cobalt  → color primario de marca
///   • Ámbar cálido       → acción / CTA secundario
///   • Verde salud        → éxito / planes activos
///
/// Material 3 · Soporte completo light + dark.
/// Dark mode: azul claro #90CAFF — alto contraste sobre fondo oscuro navy.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

// ─── Paleta de marca BampysVet ─────────────────────────────────────────────
/// Azul royal cobalt del logotipo BampysVet — color primario.
const Color kBampysBlue = Color(0xFF1853C0);

/// Variante clara para contenedores en modo claro.
const Color kBampysBlueContainer = Color(0xFFD6E4FF);

/// Ámbar cálido — acción secundaria, FABs, badges.
const Color kWarmAmber = Color(0xFFF57C00);

/// Verde salud — plan ACTIVE, éxito, confirmaciones.
const Color kHealthGreen = Color(0xFF2E7D32);

/// Rojo clínico — error, tóxico, plan devuelto.
const Color kClinicalRed = Color(0xFFB71C1C);

const _fontFamily = null;

class AppTheme {
  AppTheme._();

  // ─── Tema claro ──────────────────────────────────────────────────────────
  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: kBampysBlue,
      brightness: Brightness.light,
      primary: kBampysBlue,
      onPrimary: Colors.white,
      primaryContainer: kBampysBlueContainer,
      onPrimaryContainer: const Color(0xFF001849),
      secondary: kWarmAmber,
      secondaryContainer: const Color(0xFFFFE0B2),
      tertiary: kHealthGreen,
      tertiaryContainer: const Color(0xFFC8E6C9),
      error: kClinicalRed,
      errorContainer: const Color(0xFFFFDAD6),
      surface: const Color(0xFFF8F9FF),
      onSurface: const Color(0xFF1A1C2E),
      onSurfaceVariant: const Color(0xFF44475A),
      outline: const Color(0xFF8B8FA8),
      outlineVariant: const Color(0xFFCDCEE0),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      fontFamily: _fontFamily,

      // ── AppBar ──────────────────────────────────────────────────────────
      appBarTheme: AppBarTheme(
        backgroundColor: kBampysBlue,
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
          backgroundColor: kBampysBlue,
          foregroundColor: Colors.white,
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
          foregroundColor: kBampysBlue,
          side: const BorderSide(color: kBampysBlue, width: 1.5),
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
          foregroundColor: kBampysBlue,
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
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFCDCEE0)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFCDCEE0)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: kBampysBlue, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: kClinicalRed),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: kClinicalRed, width: 2),
        ),
        labelStyle: const TextStyle(color: Color(0xFF44475A)),
        floatingLabelStyle: const TextStyle(color: kBampysBlue),
        prefixIconColor: const Color(0xFF8B8FA8),
        suffixIconColor: const Color(0xFF8B8FA8),
      ),

      // ── Cards ───────────────────────────────────────────────────────────
      cardTheme: CardThemeData(
        elevation: 1,
        surfaceTintColor: kBampysBlue,
        color: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xFFE8ECF8), width: 0.5),
        ),
        margin: const EdgeInsets.only(bottom: 12),
        clipBehavior: Clip.antiAlias,
      ),

      // ── Chips ───────────────────────────────────────────────────────────
      chipTheme: ChipThemeData(
        backgroundColor: const Color(0xFFEEF2FF),
        selectedColor: kBampysBlueContainer,
        labelStyle: const TextStyle(fontSize: 12, color: Color(0xFF1A1C2E)),
        iconTheme: const IconThemeData(size: 16),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: const BorderSide(color: Color(0xFFCDCEE0)),
        ),
      ),

      // ── ListTile ────────────────────────────────────────────────────────
      listTileTheme: const ListTileThemeData(
        minVerticalPadding: 12,
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      ),

      // ── Divider ─────────────────────────────────────────────────────────
      dividerTheme: const DividerThemeData(
        color: Color(0xFFCDCEE0),
        thickness: 1,
        space: 1,
      ),

      // ── Snackbar ────────────────────────────────────────────────────────
      snackBarTheme: SnackBarThemeData(
        backgroundColor: const Color(0xFF1A1C2E),
        contentTextStyle:
            const TextStyle(color: Colors.white, fontSize: 14),
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),

      // ── NavigationBar ───────────────────────────────────────────────────
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: Colors.white,
        indicatorColor: kBampysBlueContainer,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const TextStyle(
              color: kBampysBlue,
              fontWeight: FontWeight.w600,
              fontSize: 12,
            );
          }
          return const TextStyle(fontSize: 12);
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: kBampysBlue);
          }
          return const IconThemeData(color: Color(0xFF8B8FA8));
        }),
      ),

      // ── Tabs ────────────────────────────────────────────────────────────
      tabBarTheme: const TabBarThemeData(
        labelColor: Colors.white,
        unselectedLabelColor: Color(0xFFB3C8F0),
        indicatorColor: Colors.white,
        indicatorSize: TabBarIndicatorSize.tab,
        labelStyle:
            TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        unselectedLabelStyle:
            TextStyle(fontWeight: FontWeight.w400, fontSize: 13),
      ),

      // ── Slider ──────────────────────────────────────────────────────────
      sliderTheme: SliderThemeData(
        activeTrackColor: kBampysBlue,
        thumbColor: kBampysBlue,
        inactiveTrackColor: kBampysBlueContainer,
        overlayColor: kBampysBlue.withAlpha(30),
        valueIndicatorColor: kBampysBlue,
        valueIndicatorTextStyle: const TextStyle(color: Colors.white),
      ),

      // ── Checkbox & Switch ────────────────────────────────────────────────
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith((states) =>
            states.contains(WidgetState.selected) ? kBampysBlue : null),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) =>
            states.contains(WidgetState.selected) ? Colors.white : null),
        trackColor: WidgetStateProperty.resolveWith((states) =>
            states.contains(WidgetState.selected) ? kBampysBlue : null),
      ),

      // ── Scaffold ────────────────────────────────────────────────────────
      scaffoldBackgroundColor: const Color(0xFFF8F9FF),

      // ── Typography ───────────────────────────────────────────────────────
      textTheme: _buildTextTheme(isDark: false),
    );
  }

  // ─── Tema oscuro ─────────────────────────────────────────────────────────
  static ThemeData get dark {
    final scheme = ColorScheme.fromSeed(
      seedColor: kBampysBlue,
      brightness: Brightness.dark,
      // En dark mode el primary debe ser CLARO para contrastar con el fondo oscuro
      primary: const Color(0xFF90CAFF),
      onPrimary: const Color(0xFF003063),
      primaryContainer: const Color(0xFF1A3A6B),
      onPrimaryContainer: const Color(0xFFD6E4FF),
      secondary: const Color(0xFFFFB74D),
      secondaryContainer: const Color(0xFF7A3A00),
      onSecondary: const Color(0xFF3E1C00),
      tertiary: const Color(0xFF81C784),
      tertiaryContainer: const Color(0xFF1B4A1E),
      error: const Color(0xFFFF8A80),
      errorContainer: const Color(0xFF7A0000),
      surface: const Color(0xFF131929),
      surfaceContainerHighest: const Color(0xFF1E2540),
      onSurface: const Color(0xFFE2E8F8),
      onSurfaceVariant: const Color(0xFFA8B4D0),
      outline: const Color(0xFF5A6890),
      outlineVariant: const Color(0xFF1E2540),
      inverseSurface: const Color(0xFFE2E8F8),
      onInverseSurface: const Color(0xFF131929),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      fontFamily: _fontFamily,

      // ── AppBar en dark ───────────────────────────────────────────────────
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFF0D1529),
        foregroundColor: Color(0xFFE2E8F8),
        elevation: 0,
        scrolledUnderElevation: 2,
        centerTitle: false,
        systemOverlayStyle: SystemUiOverlayStyle.light,
        titleTextStyle: TextStyle(
          color: Color(0xFFE2E8F8),
          fontSize: 20,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.15,
        ),
        iconTheme: IconThemeData(color: Color(0xFFE2E8F8)),
        actionsIconTheme: IconThemeData(color: Color(0xFFE2E8F8)),
      ),

      // ── Botones en dark ──────────────────────────────────────────────────
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF90CAFF),
          foregroundColor: const Color(0xFF003063),
          minimumSize: const Size.fromHeight(48),
          padding:
              const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
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
          foregroundColor: const Color(0xFF90CAFF),
          side: const BorderSide(color: Color(0xFF90CAFF), width: 1.5),
          minimumSize: const Size.fromHeight(48),
          padding:
              const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
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
          foregroundColor: const Color(0xFF90CAFF),
          minimumSize: const Size(48, 48),
          padding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
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
        fillColor: const Color(0xFF1E2540),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF1E2540)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF1E2540)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide:
              const BorderSide(color: Color(0xFF90CAFF), width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFFF8A80)),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide:
              const BorderSide(color: Color(0xFFFF8A80), width: 2),
        ),
        labelStyle: const TextStyle(color: Color(0xFFA8B4D0)),
        floatingLabelStyle: const TextStyle(color: Color(0xFF90CAFF)),
        prefixIconColor: const Color(0xFF5A6890),
        suffixIconColor: const Color(0xFF5A6890),
      ),

      // ── Cards en dark ────────────────────────────────────────────────────
      cardTheme: const CardThemeData(
        elevation: 0,
        color: Color(0xFF1E2540),
        surfaceTintColor: Color(0xFF90CAFF),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(16)),
          side: BorderSide(color: Color(0xFF2A3460), width: 1),
        ),
        margin: EdgeInsets.only(bottom: 12),
        clipBehavior: Clip.antiAlias,
      ),

      // ── Chips en dark ────────────────────────────────────────────────────
      chipTheme: ChipThemeData(
        backgroundColor: const Color(0xFF1E2540),
        selectedColor: const Color(0xFF1A3A6B),
        labelStyle: const TextStyle(
            fontSize: 12, color: Color(0xFFE2E8F8)),
        iconTheme: const IconThemeData(
            size: 16, color: Color(0xFFA8B4D0)),
        padding:
            const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: const BorderSide(color: Color(0xFF2A3460)),
        ),
      ),

      // ── ListTile en dark ─────────────────────────────────────────────────
      listTileTheme: const ListTileThemeData(
        minVerticalPadding: 12,
        contentPadding:
            EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        textColor: Color(0xFFE2E8F8),
        iconColor: Color(0xFFA8B4D0),
      ),

      // ── Divider en dark ──────────────────────────────────────────────────
      dividerTheme: const DividerThemeData(
        color: Color(0xFF1E2540),
        thickness: 1,
        space: 1,
      ),

      // ── Snackbar en dark ─────────────────────────────────────────────────
      snackBarTheme: SnackBarThemeData(
        backgroundColor: const Color(0xFF1E2540),
        contentTextStyle: const TextStyle(
            color: Color(0xFFE2E8F8), fontSize: 14),
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),

      // ── Tabs en dark ─────────────────────────────────────────────────────
      tabBarTheme: const TabBarThemeData(
        labelColor: Color(0xFF90CAFF),
        unselectedLabelColor: Color(0xFF5A6890),
        indicatorColor: Color(0xFF90CAFF),
        indicatorSize: TabBarIndicatorSize.tab,
        labelStyle:
            TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        unselectedLabelStyle:
            TextStyle(fontWeight: FontWeight.w400, fontSize: 13),
      ),

      // ── Slider en dark ───────────────────────────────────────────────────
      sliderTheme: SliderThemeData(
        activeTrackColor: const Color(0xFF90CAFF),
        thumbColor: const Color(0xFF90CAFF),
        inactiveTrackColor: const Color(0xFF1E2540),
        overlayColor: const Color(0xFF90CAFF).withAlpha(30),
        valueIndicatorColor: const Color(0xFF90CAFF),
        valueIndicatorTextStyle:
            const TextStyle(color: Color(0xFF003063)),
      ),

      // ── Scaffold en dark ─────────────────────────────────────────────────
      scaffoldBackgroundColor: const Color(0xFF131929),

      // ── Typography en dark ───────────────────────────────────────────────
      textTheme: _buildTextTheme(isDark: true),
    );
  }

  // ─── Escala tipográfica Material 3 ────────────────────────────────────────
  static TextTheme _buildTextTheme({required bool isDark}) {
    final baseColor =
        isDark ? const Color(0xFFE2E8F8) : const Color(0xFF1A1C2E);
    final subtleColor =
        isDark ? const Color(0xFFA8B4D0) : const Color(0xFF44475A);

    return TextTheme(
      displayLarge: TextStyle(
          fontSize: 57,
          fontWeight: FontWeight.w400,
          color: baseColor,
          letterSpacing: -0.25),
      displayMedium: TextStyle(
          fontSize: 45,
          fontWeight: FontWeight.w400,
          color: baseColor),
      displaySmall: TextStyle(
          fontSize: 36,
          fontWeight: FontWeight.w400,
          color: baseColor),
      headlineLarge: TextStyle(
          fontSize: 32,
          fontWeight: FontWeight.w700,
          color: baseColor),
      headlineMedium: TextStyle(
          fontSize: 28,
          fontWeight: FontWeight.w700,
          color: baseColor),
      headlineSmall: TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.w600,
          color: baseColor),
      titleLarge: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w600,
          color: baseColor,
          letterSpacing: 0),
      titleMedium: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: baseColor,
          letterSpacing: 0.15),
      titleSmall: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: baseColor,
          letterSpacing: 0.1),
      bodyLarge: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w400,
          color: baseColor,
          letterSpacing: 0.5),
      bodyMedium: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w400,
          color: baseColor,
          letterSpacing: 0.25),
      bodySmall: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w400,
          color: subtleColor,
          letterSpacing: 0.4),
      labelLarge: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: baseColor,
          letterSpacing: 0.1),
      labelMedium: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w500,
          color: subtleColor,
          letterSpacing: 0.5),
      labelSmall: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w500,
          color: subtleColor,
          letterSpacing: 0.5),
    );
  }
}
