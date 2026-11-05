# Guía funcional — Traductor Maya

## ¿Qué hace?

Es un chat donde escribes una o varias **palabras sueltas** en **español** o en **maya yucateco** y te dice cómo se dicen en el otro idioma, con su **significado** y una **frase de ejemplo**.

> Por ahora solo se usa **español ↔ maya**. El inglés está desactivado (se puede reactivar en la configuración).

Ejemplos de lo que puedes escribir:

| Escribes | Obtienes |
|---|---|
| `¿cómo se dice perro en maya?` | *Perro* se dice **peek'**, con significado y ejemplo: «El perro cuida mi casa» → «Le peek'o' ku kanáantik in wotoch.» |
| `¿qué significa ja'?` (o `ja` sin saltillo) | **agua** |
| `traduce sol, luna y agua` | las tres palabras en maya |
| una palabra que no está en el catálogo | la busca en el sitio de respaldo y avisa que no es del catálogo oficial; si tampoco está, lo dice |

## Reglas importantes

1. **Primero el catálogo.** Las traducciones salen del archivo oficial `data/catalogo.md` (500 palabras con significado y ejemplo). **Nunca inventa.**
   Si una palabra no está, consulta el sitio de respaldo [pueblosoriginarios.com](https://pueblosoriginarios.com/lenguas/mayas.php) y te avisa que viene de ahí. Las frases de ejemplo en maya del catálogo son un borrador en revisión con hablantes.
2. **Palabras sueltas, no frases.** El maya tiene su propia gramática; traducir frases completas daría errores. Si escribes una frase, el asistente te ofrece traducir sus palabras clave.
3. **Solo traducciones.** Si preguntas otra cosa (el clima, una receta…), el asistente te recuerda amablemente para qué sirve.
4. **Internet restringido.** El traductor solo puede consultar las páginas autorizadas en la configuración (`ALLOWED_SOURCES`); nada más.

## La pantalla

```
┌──────────────────────────────────────┬─────────────────────┐
│  Chat                                │  Consumo de tokens  │
│                                      │  Esta sesión        │
│  tú: ¿cómo se dice perro?            │   Asistente   420   │
│  bot: Buscando en el catálogo...     │   Traductor   380   │
│  bot: Perro se dice peek'. Ejemplo…  │                     │
│                                      │   Total       800   │
│                                      │  Hoy · Histórico    │
│  [ escribe una palabra… ] [Enviar]   │  Costo estimado $   │
└──────────────────────────────────────┴─────────────────────┘
```

### El panel de consumo

- **Token:** es un pedacito de texto (más o menos ¾ de una palabra). El servicio de IA cobra por tokens: los que **entran** (tu mensaje y las instrucciones) y los que **salen** (la respuesta).
- **Esta sesión:** lo que llevas gastado desde que abriste la página, separado por agente.
- **Hoy / Histórico:** lo que ha gastado **toda la app** (todos los usuarios).
- **Costo estimado:** tokens × precio del modelo configurado. Es una **estimación**; el cobro real lo ves en el portal de Azure (*Cost Management*).

## Clave de acceso y límites

Para que nadie gaste los créditos de Azure, la app puede pedir una **clave de acceso** al abrirla. Además hay límites:

| Límite | Valor por defecto | Qué pasa al llegar |
|---|---|---|
| Caracteres por mensaje | 300 | El mensaje se rechaza |
| Mensajes por sesión | 30 | Hay que recargar la página |
| Tokens por sesión | 40 000 | Hay que recargar la página |
| Tokens por día (toda la app) | 300 000 | La app se pausa hasta el día siguiente |
| Mensajes por minuto, por persona (IP) | 8 | Pide esperar unos segundos (evita bots) |
| Mensajes por hora, por persona (IP) | 60 | Pide esperar |

## ¿Cómo agrego palabras?

Edita `data/catalogo.md`. Es una tabla:

```markdown
| # | Español | Inglés | Maya | Explicación (español) | Explicación (maya) | Ejemplo (español) | Ejemplo (inglés) | Ejemplo (maya) |
|---|---|---|---|---|---|---|---|---|
| 1 | perro | dog | peek' | Animal doméstico que cuida la casa. | … | El perro cuida mi casa. | … | Le peek'o' ku kanáantik in wotoch. |
```

Solo son obligatorias las columnas `Español` y `Maya`. Puede haber varias tablas (por categoría).

- Usa `/` para sinónimos.
- Escribe el saltillo del maya con apóstrofo recto `'` (la app también reconoce `’`).
- No importan mayúsculas, acentos ni el saltillo al buscar (`peek` encuentra `peek'`).
- Después de editar, reinicia la app.
