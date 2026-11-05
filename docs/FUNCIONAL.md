# Guía funcional — Traductor Maya

## ¿Qué hace?

Es un chat donde escribes una o varias **palabras sueltas** y te dice cómo se dicen en **maya yucateco**, **español** o **inglés**.

Ejemplos de lo que puedes escribir:

| Escribes | Obtienes |
|---|---|
| `¿cómo se dice perro en maya?` | perro → **peek'** |
| `what does ja' mean?` | ja' → **water** (agua) |
| `traduce sol, luna y agua` | las tres palabras en maya |
| `¿cómo se dice computadora?` | aviso de que esa palabra aún no está en el catálogo |

## Reglas importantes

1. **Solo palabras del catálogo.** Todas las traducciones salen del archivo oficial `data/catalogo.md` (150–200 palabras). Si una palabra no está ahí, la app lo dice; **nunca inventa**.
2. **Palabras sueltas, no frases.** El maya tiene su propia gramática; traducir frases completas daría errores. Si escribes una frase, el asistente te ofrece traducir sus palabras clave.
3. **Solo traducciones.** Si preguntas otra cosa (el clima, una receta…), el asistente te recuerda amablemente para qué sirve.
4. **Sin internet.** El traductor no busca en la web, salvo en sitios que el administrador autorice explícitamente en la configuración.

## La pantalla

```
┌──────────────────────────────────────┬─────────────────────┐
│  Chat                                │  Consumo de tokens  │
│                                      │  Esta sesión        │
│  tú: ¿cómo se dice perro?            │   Asistente   420   │
│  bot: perro → peek'                  │   Traductor   380   │
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

## ¿Cómo agrego palabras?

Edita `data/catalogo.md`. Es una tabla:

```markdown
| Español | English | Maya | Categoría | Notas |
|---|---|---|---|---|
| perro | dog | peek' | animales | |
| maíz | corn / maize | ixi'im | alimentos | |
```

- Usa `/` para sinónimos.
- Escribe el saltillo del maya con apóstrofo recto `'` (la app también reconoce `’`).
- No importan mayúsculas ni acentos al buscar.
- Después de editar, reinicia la app.
