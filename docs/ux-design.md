# UX / Diseño — NutriVet.IA

Guía de diseño y experiencia de usuario para la app móvil NutriVet.IA.

---

## Paleta de Colores — BampysVet Brand

| Token | Hex | Rol |
|-------|-----|-----|
| `kBampysBlue` | `#1853C0` | Primario — Royal Blue extraído del logo de BampysVet |
| `kBampysBlueContainer` | `#D6E4FF` | Contenedor primario (light) |
| `kWarmAmber` | `#F57C00` | Acento — FAB, CTAs secundarios |
| `kHealthGreen` | `#2E7D32` | Éxito — planes ACTIVE, indicadores positivos |
| `kClinicalRed` | `#B71C1C` | Error — toxicidad, errores críticos |

**Fuente de verdad**: `mobile/lib/core/theme/app_theme.dart`

---

## Tema — Light Mode

- `surface`: `#F8F9FF` — blanco con toque azulado, no blanco puro (reduce fatiga visual)
- `onSurface` (texto principal): `#1A1C2E` — azul marino oscuro, no negro puro
- `primary`: `#1853C0` — Royal Blue
- `secondary`: `#F57C00` — Warm Amber
- Tarjetas: fondo `#FFFFFF`, sombra sutil M3

## Tema — Dark Mode

- `surface`: `#131929` — azul marino profundo (no negro puro)
- `onSurface`: `#E2E8F8` — blanco azulado claro (alto contraste)
- `primary`: **`#90CAFF`** — azul claro (IMPORTANTE: en dark mode el primario debe ser CLARO para contraste contra fondo oscuro)
- `primaryContainer`: `#1A3A6B` — azul oscuro para contenedores

> **Regla dark mode**: Si el primario en light es oscuro (#1853C0), en dark debe invertirse a una variante clara (#90CAFF) para mantener contraste ≥ 4.5:1 (WCAG AA).

---

## Responsive — Breakpoints

Implementado en `mobile/lib/core/utils/responsive.dart`.

| Nombre | Ancho | Comportamiento |
|--------|-------|----------------|
| Mobile | < 600dp | Layout de columna única |
| Tablet | ≥ 600dp | Contenido centrado + max-width |

```dart
class Breakpoints {
  static const double tablet = 600;
  static const double maxContentWidth = 720;  // listas, perfiles, planes
  static const double maxFormWidth = 480;     // formularios, login, wizard
}
```

**Patrón**: Siempre usar `LayoutBuilder` + `constraints.maxWidth`. Nunca verificar tipo de dispositivo ni orientación directamente.

```dart
// CORRECTO
LayoutBuilder(
  builder: (context, constraints) {
    final isTablet = constraints.maxWidth >= Breakpoints.tablet;
    return isTablet ? GridView(...) : ListView(...);
  },
)

// INCORRECTO — no usar
if (Platform.isIPad) { ... }
```

---

## Touch Targets

Todos los botones e interactivos tienen `minimumSize: Size.fromHeight(48)` o equivalente.
Estándar: Material Design ≥ 48×48dp.

```dart
// En AppTheme — aplicado globalmente
ElevatedButtonThemeData(
  style: ElevatedButton.styleFrom(
    minimumSize: const Size.fromHeight(48),
  ),
)
```

---

## Footer Global

Todas las pantallas terminan con `AppFooter` (`mobile/lib/core/widgets/app_footer.dart`).

```
Desarrollada por Sadid Romero
© {año} BampysVet · Todos los derechos reservados
```

Implementación: como último ítem del `ListView` o al final del `Column` principal.

---

## Accesibilidad

- Contraste mínimo WCAG AA (4.5:1) verificado manualmente para light y dark.
- `semanticsLabel` en iconos sin texto.
- Tamaño de texto base: 14sp (bodyMedium) — no reducir sin justificación clínica.

---

## Widgets de Layout Reutilizables

| Widget | Archivo | Uso |
|--------|---------|-----|
| `ResponsiveCenter` | `core/utils/responsive.dart` | Centra contenido con max-width |
| `ResponsiveBody` | `core/utils/responsive.dart` | SafeArea + centrado + max-width para pantallas completas |
| `AppFooter` | `core/widgets/app_footer.dart` | Footer de copyright en todas las pantallas |

---

## Rol del Veterinario — Flujo UX

1. **Registro**: selector de rol (Propietario / Veterinario) con tarjetas visuales
2. **Login**: detecta rol desde JWT → redirige a `/vet/dashboard` o `/dashboard`
3. **VetDashboard**: 2 pestañas — "Revisión" (planes PENDING_VET) y "Pacientes" (ClinicPets)
4. **Crear paciente clínico**: wizard de 13 campos → genera claim code → propietario lo usa para vincular
5. **Revisar plan**: aprobar (→ ACTIVE) o devolver con comentario obligatorio (→ PENDING_VET)

---

## Convenciones de Pantallas

- AppBar siempre con `title` descriptivo
- `Scaffold` + `body` envuelto en `Form` para pantallas con inputs
- Formularios largos: `ListView` con `padding: EdgeInsets.all(20)`
- Botón de acción principal: `ElevatedButton.icon` con ancho completo (`SizedBox(width: double.infinity)`)
- Estados de carga: `CircularProgressIndicator` dentro del botón (no pantalla completa) para acciones rápidas
- Error handling: `ScaffoldMessenger.showSnackBar` con texto descriptivo

---

## Notas de Implementación

- **Visibility toggle contraseña**: campo con `obscureText` + `IconButton` en `suffixIcon` con `Icons.visibility` / `Icons.visibility_off`
- **PageStorageKey**: pendiente de agregar en ListViews principales para preservar scroll position en navegación de tabs
- **NavigationRail**: pendiente para layout tablet en dashboard (en lugar de bottom nav)
- **Notificaciones push**: no implementado — pendiente unidad futura con FCM + firebase-admin backend + tabla `device_tokens`
