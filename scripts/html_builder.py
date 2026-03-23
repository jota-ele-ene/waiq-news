"""
html_builder.py — Genera el HTML completo del email con estilos WAIQ (waiq.css).

Siempre devuelve mode="html" con HTML autónomo (sin plantillas Brevo).
El HTML incluye los hooks de tracking de Brevo:
  - {{track_open}}   → pixel de apertura (1×1 px invisible)
  - {{unsubscribe}}  → URL de baja gestionada por Brevo

El seguimiento de clicks se habilita en mailer.py a través del campo
"tracking" del payload de la API de Brevo (header + clicks).

Tokens de diseño de /css/waiq.css:
  NAVY    = rgb(2,21,71)   textos, fondos, botones
  CYAN    = #00A8BC        acentos, h2, links, tags topics
  CYAN_LT = #9cecf5        hover, gradiente
  FONT    = tradegothiclt-bold
"""

from datetime import datetime
from scripts.config import SITE_BASE_URL, FROM_NAME

NAVY    = "rgb(2,21,71)"
CYAN    = "#00A8BC"
CYAN_LT = "#9cecf5"
FONT    = "'tradegothiclt-bold',Arial,sans-serif"

# Textos UI por idioma
_UI = {
    "es": {
        "featured":             "Artículo destacado de la semana",
        "read_more":            "Leer el artículo completo →",
        "sources":              "Fuentes",
        "digest":               "Digest · últimos {days} días",
        "unsubscribe":          "aquí",
        "manage_subscription":  "Gestionar los emails que recibes de nosotros ",
        "preferences":          "Mis preferencias",
        "footer_msg":           "Recibes esto porque eres parte de la <strong>comunidad WAIQ</strong>.",
    },
    "en": {
        "featured":             "Article of the week",
        "read_more":            "Read full article →",
        "sources":              "Sources",
        "digest":               "Digest · last {days} days",
        "unsubscribe":          "here",
        "manage_subscription":  "Manage the emails you receive from us ",
        "preferences":          "My preferences",
        "footer_msg":           "You receive this because you are part of the <strong>WAIQ community</strong>.",
    },
}


def _ui(key: str, lang: str, **kwargs) -> str:
    text = _UI.get(lang, _UI["es"]).get(key, _UI["es"][key])
    return text.format(**kwargs) if kwargs else text


# ── Componentes base ──────────────────────────────────────────────────────────

def _tag_topic(tag: str) -> str:
    return (
        f'<span style="display:inline-block;background:{CYAN};color:#ffffff;'
        f'font-size:11px;padding:2px 10px;border-radius:8px;'
        f'margin:0 4px 4px 0;letter-spacing:normal;">{tag}</span>'
    )


def _tag_area(tag: str) -> str:
    return (
        f'<span style="display:inline-block;background:#ffffff;color:{CYAN};'
        f'border:1px solid {CYAN};font-size:11px;padding:2px 10px;border-radius:8px;'
        f'margin:0 4px 4px 0;letter-spacing:normal;">{tag}</span>'
    )


def _button(url: str, label: str) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:{NAVY};color:#ffffff;'
        f'padding:10px 24px;border-radius:4px;text-decoration:none;font-weight:700;'
        f'font-size:14px;letter-spacing:1px;font-family:{FONT};">{label}</a>'
    )


def _h2(text: str) -> str:
    """h2 WAIQ: línea de 100px encima en CYAN + texto CYAN (emulado con tabla para email)."""
    return f"""
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"
      style="margin:0 0 6px;">
      <tr>
        <td style="border-top:6px solid {CYAN};width:100px;font-size:0;line-height:0;">
          &nbsp;
        </td>
      </tr>
      <tr>
        <td style="font-family:{FONT};font-size:18px;font-weight:bold;
          color:{CYAN};padding-top:6px;">
          {text}
        </td>
      </tr>
    </table>"""


def _ref_item(title: str, url: str, source: str = "", image: str = "") -> str:
    """
    Item de referencia estilo radar-ref-item:
    - border-left 3px CYAN
    - miniatura a la izquierda si hay imagen (64x64, object-fit cover)
    - título + fuente a la derecha
    """
    thumb = ""
    if image:
        thumb = f"""
        <td style="width:64px;min-width:64px;padding-right:10px;vertical-align:top;">
          <a href="{url}" style="display:block;width:64px;height:64px;overflow:hidden;
            border-radius:2px;text-decoration:none;">
            <img src="{image}" width="64" height="64"
              style="width:64px;height:64px;object-fit:cover;display:block;border:0;"
              alt="">
          </a>
        </td>"""

    content_td = f"""
        <td style="vertical-align:top;">
          <a href="{url}" style="font-family:{FONT};font-size:13px;font-weight:600;
            color:{NAVY};text-decoration:none;line-height:1.35;display:block;">
            {title}
          </a>
          {"<span style='font-size:11px;color:" + CYAN + ";opacity:0.8;letter-spacing:0.03em;display:block;margin-top:3px;'>" + source + "</span>" if source else ""}
        </td>"""

    return f"""
    <tr>
      <td style="padding:0;border-left:3px solid {CYAN};
        background:rgba(0,168,188,0.04);border-radius:2px;">
        <table role="presentation" cellpadding="10" cellspacing="0" border="0"
          width="100%">
          <tr>
            {thumb}
            {content_td}
          </tr>
        </table>
      </td>
    </tr>
    <tr><td style="height:8px;font-size:0;line-height:0;">&nbsp;</td></tr>"""


# ── Wrapper HTML autónomo (fallback sin plantilla Brevo) ─────────────────────

def _standalone_wrap(inner: str, preheader: str, lang: str) -> str:
    year = datetime.utcnow().year
    pre_tag = (
        f'<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;'
        f'font-size:1px;line-height:1px;color:#f5f5f5;">{preheader}&nbsp;</div>'
        if preheader else ""
    )
    lang_path = "es/" if lang == "es" else ""
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <title>{FROM_NAME} Newsletter</title>
</head>
<body style="margin:0;padding:0;
  font-family:{FONT};color:{NAVY};-webkit-text-size-adjust:100%;">
{pre_tag}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
        style="max-width:600px;width:100%;">

        <!-- HEADER: LOGO -->
        <tr>
          <td style="padding:32px 20% 0;text-align:center;">
            <a href="{SITE_BASE_URL}" style="text-decoration:none;display:block;color:inherit">
              <span style="font-size:0px;font-weight:normal;">
              <img style="display:block; width:100%" border="0" width="" src="https://waiq.technology/images/waiq-text.png" data-imagetype="External">
              <!--<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" class="svg-uno" viewBox="0 0 877 256"><path fill="transparent" d="M586 257H1.064V1.093h876.904V257zm-355.968-69.29c-1.282 3.813-4.25 6.912-2.245 11.804 5.1 12.437 9.513 25.155 14.21 37.758 1.952 5.238 3.928 10.468 6.441 17.16 4.734-8.398 8.773-15.235 12.498-22.238 7.28-13.691 14.32-27.51 21.577-41.213 9.778-18.464 19.653-36.875 29.51-55.297 7.972-14.899 16.048-29.743 23.954-44.677 14.588-27.557 29.086-55.162 43.615-82.736-3.92-.413-7.986-1.16-12.062-1.212-12.66-.161-25.324-.167-37.981.073-1.673.031-4.033 1.432-4.85 2.887-5.425 9.658-10.477 19.524-15.725 29.283-4.935 9.177-9.987 18.291-14.939 27.46-5.007 9.268-10.028 18.53-14.909 27.865-5.626 10.761-11.018 21.645-16.67 32.392-6.386 12.143-12.963 24.184-19.428 36.284-4.223 7.903-8.394 15.833-12.996 24.408M592.999 99.5l-.001-82.482c0-7.933 0-7.916-7.867-7.036-1.152.129-2.33.02-3.497.02h-34.633c0 39.932-.463 80.729.13 121.51.596 41.085-2.766 82.177-.289 123.487 13.857 0 27.004-.215 40.137.113 4.859.121 6.14-1.33 6.123-6.146-.17-49.488-.103-98.977-.103-149.466M429.963 76.376c2.021-4.543 4.125-9.053 6.006-13.654.48-1.171.743-2.839.28-3.926-6.954-16.297-14.047-32.536-21.51-49.716-1.385 1.903-2.75 3.283-3.534 4.937-4.33 9.152-8.475 18.391-12.767 27.562-6.499 13.887-13.14 27.708-19.587 41.619-8.25 17.798-16.392 35.647-24.536 53.494-7.383 16.18-14.662 32.409-22.073 48.576-5.89 12.852-12.033 25.59-17.833 38.482-4.288 9.533-8.203 19.234-12.26 28.802h45.704c27.336-58.777 54.492-117.165 82.11-176.176m434.507 138.63c-3.428-3.77-6.718-7.676-10.308-11.284-19.721-19.818-39.522-39.557-59.278-59.342-2.39-2.394-4.828-6.98-6.965-6.82-2.684.2-5.076 4.251-7.6 6.636-8.829 8.347-17.66 16.692-26.531 25.075 13.902 13.902 27.407 27.228 40.707 40.757 13.363 13.594 26.522 27.39 39.784 41.11l33.944-32.55c-1.32-1.257-2.285-2.174-3.753-3.583" class="bg"/><path fill="#00A8BC" d="M230.236 187.382c4.398-8.246 8.57-16.176 12.792-24.079 6.465-12.1 13.042-24.141 19.428-36.284 5.652-10.747 11.044-21.63 16.67-32.392 4.88-9.335 9.902-18.597 14.91-27.866 4.951-9.168 10.003-18.282 14.938-27.459 5.248-9.759 10.3-19.625 15.725-29.283.817-1.455 3.177-2.856 4.85-2.887 12.657-.24 25.321-.234 37.98-.073 4.077.052 8.143.799 12.063 1.212-14.53 27.574-29.027 55.18-43.615 82.736-7.906 14.934-15.982 29.778-23.954 44.677-9.857 18.422-19.732 36.833-29.51 55.297-7.257 13.703-14.297 27.522-21.577 41.213-3.725 7.003-7.764 13.84-12.498 22.238-2.513-6.692-4.489-11.922-6.44-17.16-4.698-12.603-9.11-25.321-14.21-37.758-2.007-4.892.962-7.991 2.448-12.132M593 100c-.001 49.989-.069 99.478.102 148.966.017 4.816-1.264 6.267-6.123 6.146-13.133-.328-26.28-.113-40.137-.113-2.477-41.31.885-82.402.289-123.487-.593-40.781-.13-81.578-.13-121.51h34.633c1.167 0 2.345.109 3.497-.02 7.866-.88 7.866-.897 7.867 7.036zM429.732 76.688c-27.387 58.7-54.543 117.087-81.879 175.864H302.15c4.057-9.568 7.972-19.269 12.26-28.802 5.8-12.892 11.943-25.63 17.833-38.482 7.411-16.167 14.69-32.396 22.073-48.576 8.144-17.847 16.286-35.696 24.536-53.494 6.448-13.91 13.088-27.732 19.587-41.62 4.292-9.17 8.437-18.41 12.767-27.56.783-1.655 2.149-3.035 3.534-4.938 7.463 17.18 14.556 33.419 21.51 49.716.463 1.087.2 2.755-.28 3.926-1.881 4.6-3.985 9.11-6.237 13.966" class="block"/><path fill="transparent" d="M481 254H1c0-80.355 0-160.71.301-241.823 4.427 6.38 8.586 13.498 12.668 20.66A1095 1095 0 0 1 25.943 54.41c1.685 3.458 3.32 6.546 5.007 10.001 12.229 23.117 24.486 45.825 36.554 68.632 8.639 16.325 17.038 32.776 25.517 49.185a3088 3088 0 0 1 16.918 33.185c4.375 8.48 8.697 16.59 13.047 24.929.028.229.184.664.13.93.242.451.537.637.85.784.02-.039-.058 0-.015.306.343.766.643 1.225.995 2.049 1.318 2.475 2.583 4.586 4.275 7.41 1.478-2.694 2.81-4.672 3.7-6.833 2.462-5.98 4.592-12.1 7.142-18.041 1.74-4.056 3.965-7.904 6.315-11.998 1.71-3.754 3.08-7.356 4.526-11.174.075-.216.133-.67.393-.751.347-.392.433-.703.596-1.4 3.678-9.374 6.82-18.572 12.379-26.741.365-.26.46-.569.628-1.19.096-.736.117-1.162.453-1.714.395-.92.475-1.715.53-2.275-.026.234.442.191.74.049 3.265-7.35 6.234-14.556 9.284-22.137 5.176-11.061 10.27-21.747 15.439-32.588 11.82 26.944 23.68 53.98 35.594 81.398.886 2.487 1.718 4.592 2.55 6.697l1.21.146c.803-2.076 1.606-4.153 2.747-6.393 1.957-4.802 3.284-9.569 5.258-14.05 3.563-8.09 7.694-15.931 11.224-24.034 1.71-3.926 4.82-7.563 2.16-12.67-3.757-7.22-6.813-14.808-10.107-22.266-8.288-18.769-16.58-37.536-24.791-56.338-4.806-11.003-9.469-22.068-14.18-33.112-3.608-8.46-7.19-16.932-10.984-25.872l-62.239 137.962c-8.795-16.492-17.101-32.075-25.415-47.654-4.538-8.504-8.96-17.074-13.67-25.481-4.659-8.316-9.79-16.368-14.38-24.72-2.989-5.438-5.222-11.286-8.073-16.805-4.18-8.093-8.58-16.074-12.983-24.05-.434-.786-1.532-1.678-2.348-1.704-4.976-.158-9.959-.08-14.94-.08L1 6V1.001h872.844V254c-31.265 0-62.588 0-94.676-.332 7.439-3.612 15.763-6.626 23.823-10.232 14.649-6.555 26.26-17.348 36.695-29.062 10.527-11.817 18.893-25.41 23.022-40.892 3.101-11.63 5.615-23.52 7.022-35.456.817-6.922-1.136-14.157-1.725-21.261-1.531-18.45-9.017-34.732-18.17-50.433-5.15-8.834-12.288-15.92-19.742-22.742-4.526-4.144-8.646-8.892-13.676-12.293-11.21-7.581-23.342-13.763-36.58-16.719-10.585-2.363-21.527-4.217-32.317-4.255-10.106-.037-20.565 1.457-30.256 4.336-15.592 4.632-30.422 11.75-42.761 22.561-17.822 15.616-31.888 34.016-38.668 57.286-4.472 15.347-7.393 30.693-6.058 46.899.803 9.755 2.364 19.328 5 28.563 3.83 13.422 10.22 25.783 18.688 37.09 16.711 22.313 37.887 37.928 65.073 45.008.613.16.98 1.268 1.462 1.934-63.689 0-127.377 0-191.618-.35-2.213-4.24-3.75-8.186-5.557-12.005-3.588-7.584-7.323-15.097-10.92-23.008-1.57-3.495-3.217-6.62-4.893-9.976-.028-.23-.184-.666-.13-.932-.24-.451-.536-.637-.85-.784-.019.039.058.001.015-.38-.69-2.141-1.338-3.9-2.009-5.618-.023.04.058-.007.013-.322-.365-.786-.685-1.258-1.032-2.108-1.023-2.73-1.939-5.12-3.03-7.427-6.634-14.043-13.43-28.013-19.941-42.113-8.257-17.881-16.26-35.88-24.44-53.797-4.458-9.764-9.095-19.446-13.583-29.196-7.377-16.023-14.605-32.117-22.149-48.06-1.065-2.251-3.558-3.826-5.821-6.158-7.404 16.908-14.26 32.43-20.932 48.031-.58 1.358-.443 3.454.185 4.83 5.132 11.245 10.487 22.389 15.724 33.586 14.007 29.944 27.94 59.923 42.024 89.831 2.649 5.625 6.138 10.856 8.74 16.5 4.019 8.712 7.606 17.623 11.296 26.82 1.897 4.155 3.874 7.94 5.874 11.685.022-.038-.056.005-.016.349.34 1.112.64 1.88.995 3.016C479 249.188 480 251.594 481 254"/><path fill="currentcolor" d="M720.469 254c-.951-.666-1.318-1.774-1.931-1.934-27.186-7.08-48.362-22.695-65.073-45.008-8.468-11.307-14.857-23.668-18.688-37.09-2.636-9.235-4.197-18.808-5-28.563-1.335-16.206 1.586-31.552 6.058-46.9 6.78-23.27 20.846-41.67 38.668-57.285 12.34-10.812 27.169-17.93 42.76-22.561 9.692-2.88 20.15-4.373 30.257-4.336 10.79.038 21.732 1.892 32.316 4.255 13.239 2.956 25.371 9.138 36.581 16.719 5.03 3.401 9.15 8.15 13.676 12.293 7.454 6.822 14.591 13.908 19.742 22.742 9.153 15.701 16.639 31.983 18.17 50.433.59 7.104 2.542 14.34 1.725 21.261-1.407 11.936-3.92 23.827-7.022 35.456-4.129 15.482-12.495 29.075-23.022 40.892-10.436 11.714-22.046 22.507-36.695 29.062-8.06 3.606-16.384 6.62-24.29 10.232-19.055.332-38.41.332-58.232.332M708.006 75.013s.072.037-.737.007c-4.898-.185-6.674 2.823-7.35 7.549-.186.306-.458.462-1.506.504-.766 1.322-1.533 2.645-2.414 4.693-4.802 3.038-6.147 8.305-8.339 13.008-4.686 10.052-7.548 20.607-7.565 31.72-.007 4.125 1.393 8.233 1.809 12.383 2.129 21.27 12.125 37.99 30.03 49.346 13.812 8.76 28.877 13.07 45.822 10.99 19.928-2.446 35.476-12.098 46.755-27.676 13.139-18.146 17.682-38.913 12.47-61.208-3.16-13.518-9.839-25.334-19.488-35.044-7.113-7.157-15.73-12.44-25.527-16.012-12.132-4.423-24.097-5.237-36.603-2.47-9.7 2.146-18.301 6.43-26.608 11.74-.237.18-.473.361-.75.47M165.039 172.106c-.022.425-.043.85-.315 1.682-.47.573-.627.785-.723 1.044-5.288 8.22-8.43 17.418-12.3 26.926-.502.746-.634 1.022-.664 1.347 0 0-.058.454-.47.738-1.785 3.942-3.158 7.6-4.53 11.259-2.009 3.94-4.234 7.789-5.974 11.845-2.55 5.94-4.68 12.06-7.142 18.04-.89 2.162-2.222 4.14-3.7 6.834-1.692-2.824-2.957-4.935-4.03-7.579-.299-1.084-.791-1.635-1.283-2.186 0 0 .078-.039-.004-.223-.226-.473-.444-.687-.734-.827 0 0-.156-.435-.173-1.065-2.229-6.093-4.134-11.71-6.773-16.957-1.489-2.96-4.185-5.314-6.338-7.94-5.62-10.94-11.219-21.89-16.865-32.816-8.479-16.409-16.878-32.86-25.517-49.185-12.068-22.807-24.325-45.515-36.287-68.834-.314-4.53-.665-8.593-5.325-10.169-3.971-7.07-7.908-14.159-11.923-21.204C9.887 25.675 5.728 18.557 1.3 11.71 1 10.286 1 8.571 1 6.428 13.327 6 25.653 6.001 37.98 6.001c4.98 0 9.963-.077 14.939.081.816.026 1.914.918 2.348 1.705 4.403 7.975 8.803 15.956 12.983 24.049 2.85 5.52 5.084 11.367 8.073 16.805 4.59 8.352 9.721 16.404 14.38 24.72 4.71 8.407 9.132 16.977 13.67 25.48 8.314 15.58 16.62 31.163 25.415 47.655L192.027 8.534c3.794 8.94 7.376 17.412 10.985 25.872 4.71 11.044 9.373 22.109 14.179 33.112 8.211 18.802 16.503 37.57 24.791 56.338 3.294 7.458 6.35 15.046 10.108 22.266 2.658 5.107-.45 8.744-2.16 12.67-3.531 8.103-7.662 15.944-11.225 24.033-1.974 4.482-3.301 9.249-5.608 14.068-2.529-.163-4.37-.506-6.211-.85l-35.54-81.015c-5.169 10.841-10.263 21.527-15.77 32.654a668 668 0 0 0-10.193 20.624c-.148.31.607 1.05.942 1.59 0 0-.468.042-.765.172-.371.766-.446 1.402-.521 2.038M471.171 230.994c-3.77-8.827-7.356-17.738-11.374-26.45-2.603-5.644-6.092-10.875-8.74-16.5-14.084-29.908-28.018-59.887-42.025-89.83-5.237-11.198-10.592-22.342-15.724-33.587-.628-1.376-.766-3.472-.185-4.83 6.672-15.6 13.528-31.123 20.932-48.03 2.263 2.33 4.756 3.906 5.821 6.156 7.544 15.944 14.772 32.038 22.149 48.061 4.488 9.75 9.125 19.432 13.583 29.196 8.18 17.917 16.183 35.916 24.44 53.797 6.511 14.1 13.307 28.07 19.942 42.113 1.09 2.307 2.006 4.696 2.932 7.69.345 1.147.76 1.654 1.174 2.16 0 0-.081.047-.075.426.693 2.113 1.381 3.846 2.07 5.58 0 0-.078.038.003.223.227.472.445.685.734.826 0 0 .156.436.174 1.083.422 3.163.548 5.776 1.376 8.144.31.888 2.252 1.206 3.45 1.784 3.674 7.542 7.41 15.055 10.997 22.639 1.806 3.82 3.344 7.766 5.09 12.005-15.27.35-30.623.35-46.446.35-1.469-2.406-2.469-4.812-3.252-7.781-.291-1.43-.8-2.298-1.307-3.165 0 0 .078-.043.072-.403-1.94-4.126-3.876-7.891-5.81-11.657" class="block"/><path fill="currentcolor" d="M109.94 215.413c2.099 2.257 4.795 4.61 6.284 7.571 2.639 5.248 4.544 10.864 6.745 16.727-4.333-7.709-8.655-15.819-13.03-24.298M166.622 169.753c-.632-.398-1.387-1.136-1.24-1.447 3.2-6.756 6.5-13.465 10.112-20.248-2.637 7.14-5.606 14.346-8.872 21.695M226.94 196.426c1.787-.04 3.628.304 5.819.63-.453 2.06-1.256 4.137-2.06 6.213l-1.21-.146c-.83-2.105-1.663-4.21-2.549-6.697M511.904 218.637c-1.274-.209-3.216-.527-3.526-1.415-.828-2.368-.954-4.981-1.348-7.914 1.658 2.708 3.304 5.834 4.874 9.329M25.943 54.41c4.61 1.206 4.96 5.27 5.221 9.432-1.902-2.886-3.536-5.974-5.221-9.432M471.092 231.364c2.014 3.396 3.95 7.161 5.868 11.325-1.994-3.386-3.97-7.17-5.868-11.325M146.378 214.949c1.031-3.506 2.404-7.164 4.113-10.89-1.033 3.534-2.402 7.136-4.113 10.89M506.047 206.565c-.645-1.353-1.333-3.086-2.003-5.24.665 1.34 1.313 3.099 2.003 5.24M476.95 243.398c.468.523.976 1.39 1.211 2.453-.572-.573-.871-1.341-1.21-2.453M123.951 242.362c.449.245.941.796 1.188 1.515-.545-.29-.845-.75-1.188-1.515M504.051 200.625c-.37-.191-.784-.698-1.102-1.467.417.21.737.68 1.102 1.467M165.353 171.98c-.24-.51-.164-1.146.234-2.146.241.43.16 1.224-.234 2.145M506.882 207.729c-.343.125-.561-.088-.769-.598.233-.039.528.147.77.598M151.297 203.024c-.23-.244-.098-.52.328-.88.105.177.019.488-.328.88M164.272 174.883c-.175-.31-.018-.522.378-.784.082.215-.013.525-.378.784M123.116 241.272c.344-.126.562.088.77.6-.233.037-.528-.149-.77-.6" class="block"/><path fill="transparent" d="M708.995 74.824c8.067-5.59 16.668-9.875 26.368-12.02 12.506-2.768 24.47-1.954 36.603 2.47 9.796 3.57 18.414 8.854 25.527 16.01 9.65 9.711 16.327 21.527 19.487 35.045 5.213 22.295.67 43.062-12.469 61.208-11.28 15.578-26.827 25.23-46.755 27.676-16.945 2.08-32.01-2.23-45.822-10.99-17.905-11.356-27.901-28.075-30.03-49.346-.416-4.15-1.816-8.258-1.81-12.383.018-11.113 2.88-21.668 7.566-31.72 2.192-4.703 3.537-9.97 8.708-13.486 1.157-1.735 1.946-2.993 2.735-4.251.358-.006.63-.162 1.193-.829a3717 3717 0 0 1 7.782-7.158s-.072-.037.19-.052c.26-.014.727-.174.727-.174"/><path fill="currentcolor" d="M707.674 75.035c-2.064 2.281-4.532 4.547-7.32 6.936.24-4.128 2.017-7.136 7.32-6.936M698.758 83.055c-.444 1.24-1.233 2.498-2.333 3.87.455-1.207 1.222-2.53 2.333-3.87M708.875 74.684c.12.14-.346.3-.588.35-.005-.13.231-.31.588-.35" class="block"/><path fill="#00A8BC" d="M864.722 215.25c1.216 1.164 2.181 2.081 3.5 3.337L834.28 251.14c-13.262-13.722-26.42-27.517-39.784-41.11-13.3-13.53-26.805-26.856-40.707-40.758 8.87-8.383 17.702-16.728 26.532-25.075 2.523-2.385 4.915-6.436 7.599-6.637 2.137-.16 4.575 4.427 6.965 6.821 19.756 19.785 39.557 39.524 59.278 59.342 3.59 3.608 6.88 7.515 10.56 11.529" class="block"/></svg>-->  
              </span>
            </a>
          </td>
        </tr>

        <!-- NAVBAR -->
        <tr>
          <td style="padding:8px 24px 10px;text-align:center;">
            <a href="{SITE_BASE_URL}/{lang_path}topics/ai"
              style="color:inherit;font-size:11px;letter-spacing:8px;
              text-decoration:none;padding:0 8px;">AI</a>
            <a href="{SITE_BASE_URL}/{lang_path}topics/web3"
              style="color:inherit;font-size:11px;letter-spacing:8px;
              text-decoration:none;padding:0 8px;">WEB3</a>
            <a href="{SITE_BASE_URL}/{lang_path}topics/quantum"
              style="color:inherit;font-size:11px;letter-spacing:8px;
              text-decoration:none;padding:0 8px;">QUANTUM</a>
          </td>
        </tr>

        <!-- CUERPO -->
        <tr>
          <td style="padding:32px 0 24px;">
            {inner}
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="padding:28px 32px 24px;text-align:center;border-top:none;">

            <!-- Subscription management -->
            <table role="presentation" cellpadding="0" cellspacing="0" border="0"
              width="100%" style="margin-bottom:20px;">
              <tr>
                <td style="border-top:1px solid rgba(0,168,188,0.3);
                  padding-top:20px;text-align:center;">
                   <p style="font-family:{FONT};font-size:10px;margin:0 0 6px;">
                    {_ui("footer_msg", lang)}
                   </p>
                  <p style="font-family:{FONT};font-size:10px;margin:0 0 12px;">
                    {_ui("manage_subscription", lang)}<a href="{SITE_BASE_URL}/pages/subscription.html?id={{{{contact.EXT_ID}}}}"
                    style="display:inline-block;text-decoration:none;color: #00A8BC;font-weight:bold;">
                    {_ui("unsubscribe", lang)}</a>
                  </p>
                  <a href="{{{{unsubscribe}}}}"
                    style="display:none;font-family:{FONT};font-size:11px;
                    letter-spacing:2px;color:rgba(255,255,255,0.55);
                    text-decoration:none;border:1px solid rgba(0,168,188,0.4);
                    padding:6px 18px;border-radius:3px;margin:0 4px 6px;">
                    {_ui("unsubscribe", lang)}
                  </a>
                </td>
              </tr>
            </table>

            <!-- Legal / brand line -->

            <p style="font-family:{FONT};font-size:10px;color:rgba(255,255,255,0.3);
              margin:0;letter-spacing:1px;">
              © {year} WAIQ · <a href="{SITE_BASE_URL}"
                style="color:rgba(255,255,255,0.3);text-decoration:none;">waiq.co</a>
            </p>

          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
<!-- Brevo open-tracking pixel -->
<img src="{{track_open}}" width="1" height="1" border="0"
  style="display:none;max-height:0;overflow:hidden;" alt="">
</body>
</html>"""


# ── Single ────────────────────────────────────────────────────────────────────

def _md_to_html(md: str) -> str:
    """
    Convierte markdown básico a HTML inline compatible con email.
    Cubre: párrafos, negrita, cursiva, links (convertidos a texto+footnote),
    y elimina headings (no apropiados en email).
    """
    if not md:
        return ""
    import re

    # Eliminar headings (# ## ###)
    md = re.sub(r"^#{1,6}\s+(.+)$", r"\1", md, flags=re.MULTILINE)

    # Negrita **texto** o __texto__
    md = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", md)
    md = re.sub(r"__(.+?)__",     r"<strong>\1</strong>", md)

    # Cursiva *texto* o _texto_
    md = re.sub(r"\*(.+?)\*", r"<em>\1</em>", md)
    md = re.sub(r"_(.+?)_",   r"<em>\1</em>", md)

    # Links [texto](url) → href 
    md = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: (
            f'<a href="{m.group(2)}" style="color:{CYAN};text-decoration:none;'
            f'font-weight:600;">{m.group(1)}</a>'
        ),
        md
    )

    # Párrafos: separar bloques por líneas en blanco
    paragraphs = re.split(r"\n{2,}", md.strip())
    html = "".join(
        f'<p style="margin:0 0 14px;">{p.strip().replace(chr(10), " ")}</p>'
        for p in paragraphs if p.strip()
    )
    return html

def _references_block(references: list[dict], lang: str) -> str:
    if not references:
        return ""
    rows = "".join(
        _ref_item(
            ref.get("title", "Ver fuente"),
            ref.get("url", "#"),
            ref.get("source", ref.get("domain", "")),
            ref.get("image", ""),
        )
        for ref in references[:10]
    )
    return f"""
    <div style="margin-top:32px;padding-top:20px;
      border-top:1px solid rgba(0,168,188,0.2);">
      <p style="font-family:{FONT};font-size:10px;font-weight:700;
        letter-spacing:5px;color:{CYAN};text-transform:uppercase;
        margin:0 0 14px;">{_ui("sources", lang)}</p>
      <table role="presentation" width="100%" cellpadding="0"
        cellspacing="0" border="0">
        {rows}
      </table>
    </div>"""


def _single_body(post: dict, lang: str) -> str:
    description = post.get("description", "")
    url         = post.get("url", SITE_BASE_URL)
    title       = post.get("title", "")
    references  = post.get("references", []) or []
    date_obj    = post.get("date")
    date_str    = date_obj.strftime("%d/%m/%Y") if date_obj else ""
    body_html   = _md_to_html(post.get("body", ""))

    # Bloques opcionales calculados ANTES del f-string para evitar
    # conflictos de comillas simples/dobles dentro de style=""
    title_block = (
        f'<h1 style="font-family:{FONT};font-size:22px;font-weight:700;'
        f'line-height:1.25;color:{NAVY};margin:0 0 10px;">'
        f'{title}</h1>'
    ) if title else ""

    date_block = (
        f'<p style="font-family:{FONT};font-size:11px;color:{CYAN};'
        f'letter-spacing:3px;margin:0 0 16px;text-transform:uppercase;">'
        f'{date_str}</p>'
    ) if date_str else ""

    body_block = (
        f'<div style="font-family:{FONT};'
        f'margin:0 0 28px;text-align:justify;">'
        f'{body_html}</div>'
    ) if body_html else ""

    return f"""
    <!--
    <p style="font-family:{FONT};font-size:10px;font-weight:700;
      letter-spacing:5px;color:{NAVY};text-transform:uppercase;
      margin:0 0 20px;padding-bottom:10px;
      border-bottom:1px solid rgba(0,168,188,0.2);">
      {_ui("featured", lang)}
    </p>
    -->

    {title_block}

    {date_block}

    <p style="font-family:{FONT};font-sstyle:italic;
      color:{NAVY};margin:0 0 24px;text-align:justify;
      border-left:3px solid {CYAN};padding-left:14px;">
      {description}
    </p>

    {body_block}

    <!--
    <div style="margin-bottom:32px;">
      {_button(url, _ui("read_more", lang))}
    </div>
    -->

    {_references_block(references, lang)}
    """

def build_single_html(post: dict, lang: str = "es") -> dict:
    subject   = f"✦ {post.get('title', 'The WAIQ State of Play')}"
    preheader = post.get("description", "")[:90]
    body      = _single_body(post, lang)
    return {
        "mode":      "html",
        "subject":   subject,
        "preheader": preheader,
        "html":      _standalone_wrap(body, preheader, lang),
    }


# ── Digest ────────────────────────────────────────────────────────────────────

def _section_block(section: dict, lang: str) -> str:
    title   = section.get("title", "")
    emoji   = section.get("emoji", "")
    summary = section.get("summary", "")
    items   = section.get("items", [])

    rows = "".join(
        _ref_item(
            item.get("label", item.get("title", "Ver fuente")),
            item.get("url", "#"),
            item.get("domain", item.get("source", "")),
            item.get("image", ""),
        )
        for item in items
    )

    return f"""
    <div style="margin-bottom:36px;">
      {_h2(f"{emoji} {title}")}
      <p style="font-family:{FONT};font-size:14px;line-height:1.65;
        color:rgba(2,21,71,0.8);margin:12px 0 16px;text-align:justify;">
        {summary}
      </p>
      <table role="presentation" width="100%" cellpadding="0"
        cellspacing="0" border="0">
        {rows}
      </table>
    </div>"""


def _digest_body(content: dict, lang: str, days: int) -> str:
    editorial     = content.get("editorial", "")
    sections      = content.get("sections", [])
    closing       = content.get("closing", "")
    sections_html = "".join(_section_block(s, lang) for s in sections)

    return f"""
    <!-- Eyebrow -->
    <p style="font-family:{FONT};font-size:10px;font-weight:700;
      letter-spacing:5px;color:{NAVY};text-transform:uppercase;
      margin:0 0 20px;padding-bottom:10px;
      border-bottom:1px solid rgba(0,168,188,0.2);">
      {_ui("digest", lang, days=days)}
    </p>

    <!-- Editorial -->
    <p style="font-family:{FONT};font-size:15px;line-height:1.75;
      color:{NAVY};margin:0 0 32px;text-align:justify;
      border-left:3px solid {CYAN};padding-left:16px;">
      {editorial}
    </p>

    <!-- Separador -->
    <div style="border-top:6px solid {NAVY};width:100px;
      margin:0 0 32px;font-size:0;line-height:0;">&nbsp;</div>

    {sections_html}

    {"<p style='font-family:" + FONT + ";font-size:13px;line-height:1.6;color:rgba(2,21,71,0.55);margin:0;padding-top:20px;border-top:1px solid rgba(0,168,188,0.2);letter-spacing:0.5px;'>" + closing + "</p>" if closing else ""}
    """


def build_digest_html(content: dict, lang: str = "es", days: int = 15) -> dict:
    subject   = content.get("subject", "✦ WAIQ Digest")
    preheader = content.get("preheader", "")
    body      = _digest_body(content, lang, days)
    return {
        "mode":      "html",
        "subject":   subject,
        "preheader": preheader,
        "html":      _standalone_wrap(body, preheader, lang),
    }