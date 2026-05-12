#!/usr/bin/env python3
"""
ga4_setup.py — Configura GA4 para HdD PWA tracking
Uso: python3 ga4_setup.py

Requiere: client_secrets.json en la misma carpeta (ver instrucciones en pantalla)
Instala deps si faltan: pip3 install google-analytics-admin google-auth-oauthlib
"""

import json
import os
import sys

PROPERTY_ID = "properties/534765544"
SCOPES = ["https://www.googleapis.com/auth/analytics.edit"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "client_secrets.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), ".ga4_token.json")


def get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None

    # Reutilizar token guardado si existe y es válido
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            pass

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception:
            pass

    # Primera vez: OAuth2 via navegador
    if not os.path.exists(CREDENTIALS_FILE):
        print("\n  ❌  Falta client_secrets.json\n")
        print("  Pasos (1 minuto):")
        print("  1. Abre: https://console.cloud.google.com/apis/credentials?project=hdd-analytics")
        print("     (si ese proyecto no existe, cualquier proyecto Google Cloud sirve)")
        print("  2. Haz clic en '+ CREAR CREDENCIALES' → 'ID de cliente de OAuth'")
        print("  3. Tipo de aplicación: 'Aplicación de escritorio'")
        print("  4. Nombre: 'HdD GA4 Setup' → Crear")
        print("  5. Descarga el JSON → guárdalo como: client_secrets.json")
        print("     en la misma carpeta que este script")
        print(f"\n  Carpeta: {os.path.dirname(os.path.abspath(__file__))}\n")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_console()
    _save_token(creds)
    return creds


def _save_token(creds):
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else [],
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)


def create_conversion_event(client, event_name):
    from google.analytics.admin_v1alpha.types import ConversionEvent
    try:
        result = client.create_conversion_event(
            parent=PROPERTY_ID,
            conversion_event=ConversionEvent(event_name=event_name)
        )
        print(f"  ✅  Conversión creada: {event_name}")
        return result
    except Exception as e:
        err = str(e)
        if "already exists" in err.lower() or "409" in err:
            print(f"  ✓   Conversión ya existía: {event_name}")
        else:
            print(f"  ⚠️   Error en {event_name}: {err}")


def create_custom_dimension(client, name, param, description):
    from google.analytics.admin_v1alpha.types import CustomDimension
    try:
        result = client.create_custom_dimension(
            parent=PROPERTY_ID,
            custom_dimension=CustomDimension(
                parameter_name=param,
                display_name=name,
                description=description,
                scope=CustomDimension.DimensionScope.EVENT,
            )
        )
        print(f"  ✅  Dimensión creada: {name} ({param})")
        return result
    except Exception as e:
        err = str(e)
        if "already exists" in err.lower() or "409" in err:
            print(f"  ✓   Dimensión ya existía: {name}")
        else:
            print(f"  ⚠️   Error en {name}: {err}")


def list_existing_conversions(client):
    try:
        events = client.list_conversion_events(parent=PROPERTY_ID)
        return {e.event_name for e in events}
    except Exception:
        return set()


def main():
    print("\n" + "=" * 60)
    print("  HdD — GA4 PWA Tracking Setup")
    print("=" * 60)

    try:
        from google.analytics import admin_v1alpha
        from google.auth.transport.requests import Request
    except ImportError:
        print("\n  Instalando dependencias...")
        os.system("pip3 install google-analytics-admin google-auth-oauthlib -q")
        from google.analytics import admin_v1alpha

    print("\n  Autenticando con Google Analytics...")
    creds = get_credentials()
    print("  ✅  Autenticado correctamente\n")

    # Cliente con credenciales OAuth2
    from google.analytics.admin_v1alpha.services.analytics_admin_service.transports import grpc as grpc_transport
    import google.auth.credentials

    client = admin_v1alpha.AnalyticsAdminServiceClient(credentials=creds)

    # ── 1. Conversiones ──────────────────────────────────────
    print("  Configurando eventos de conversión...")
    create_conversion_event(client, "pwa_installed")
    create_conversion_event(client, "pwa_install_prompt")

    # ── 2. Dimensiones personalizadas ────────────────────────
    print("\n  Creando dimensiones personalizadas...")
    create_custom_dimension(
        client,
        name="PWA Browser",
        param="browser",
        description="Navegador desde el que se instaló la PWA"
    )
    create_custom_dimension(
        client,
        name="PWA Install Outcome",
        param="outcome",
        description="Resultado del diálogo de instalación (accepted/dismissed)"
    )
    create_custom_dimension(
        client,
        name="Display Mode",
        param="display_mode",
        description="Modo de pantalla al iniciar la app (standalone/browser)"
    )

    # ── 3. Verificar propiedad ────────────────────────────────
    print("\n  Verificando propiedad GA4...")
    try:
        prop = client.get_property(name=PROPERTY_ID)
        print(f"  ✅  Propiedad: {prop.display_name} ({PROPERTY_ID})")
    except Exception as e:
        print(f"  ⚠️   No se pudo verificar propiedad: {e}")

    print("\n" + "=" * 60)
    print("  ✅  Configuración completada")
    print("\n  Para ver los datos en GA4:")
    print("  https://analytics.google.com/analytics/web/#/p534765544/reports/")
    print("  Eventos → pwa_installed, pwa_install_prompt, pwa_session")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
