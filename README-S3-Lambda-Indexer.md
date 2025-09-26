# 📘 README – Parte 1: Almacenamiento en S3 + Lambda Indexer

Este módulo define la **arquitectura base** para manejar documentos en **Amazon Web Services (AWS)** y mantener actualizada la **base vectorial (RAG)**.  

En esta fase solo se implementa:  
1. **S3 como almacenamiento canónico de documentos**.  
2. **Lambda Indexer** que se dispara automáticamente cuando se sube/borra un archivo en S3.  

---

## 🎯 Objetivo
- Guardar documentos en S3 de forma segura y versionada.  
- Disparar automáticamente un **pipeline de indexación** cuando se detecta un cambio (alta, modificación o borrado).  
- Construir/actualizar la base vectorial sin intervención manual.  
- Mantener un **puntero atómico** (`published_index_version`) para garantizar que el chatbot RAG siempre responda con un índice estable.  

---

## 📂 Componentes principales

### 1. **S3 – Almacenamiento canónico**
- Bucket sugerido: `workserver-kb`  
- Configuración:
  - **Versioning ON**  
  - Carpetas por cliente/categoría: `raw/{cliente}/{categoria}/archivo.ext`  
- Metadatos básicos:
  - `canonical_doc_id` → ruta estable del documento.  
  - `content_hash` → hash del contenido normalizado (para detectar cambios reales).  
  - `updated_at` → timestamp ISO.  
  - `source="s3"`  

### 2. **Lambda Indexer**
Se activa con eventos `ObjectCreated` y `ObjectRemoved` del bucket.  
Responsabilidades:  
- Leer archivo desde S3.  
- Normalizar texto (PDF, DOCX, etc.).  
- Cortar en chunks deterministas.  
- Generar embeddings con **OpenAI**.  
- Hacer **upsert/delete** en la base vectorial.  
- Publicar un **nuevo `index_version`** cuando el proceso termina OK.  
- Registrar métricas y errores.  

### 3. **Base vectorial (en esta fase)**
- **Dev**: Chroma/FAISS persistido en S3 (archivos).  
- **Producción futura**: OpenSearch Serverless o pgvector (RDS).  
- Reglas:
  - **upsert** por `chunk_id`.  
  - **delete** cuando un objeto de S3 es borrado.  

### 4. **Observabilidad**
- Logs en **CloudWatch**.  
- Métricas mínimas:  
  - `indexed_chunks_total`  
  - `index_errors_total`  
  - `index_build_time_ms`  
- Alarma simple: si `index_errors_total > 0` durante N minutos → aviso.  

---

## 🔒 Permisos mínimos (IAM)

**Lambda Indexer** necesita:  
- `s3:GetObject`, `s3:ListBucket` en `workserver-kb`.  
- `s3:PutObject` en `workserver-kb` (si persisto índice).  
- `ssm:GetParameter` para leer `OPENAI_API_KEY`.  
- `cloudwatch:PutMetricData` (opcional, métricas custom).  

---

## 🧪 Casos de prueba funcionales

1. **Alta de documento**: subir `devolucion.pdf` → se crean chunks → índice actualizado.  
2. **Actualización parcial**: reemplazar archivo con cambios → solo se re-embeben los chunks modificados.  
3. **Borrado**: eliminar archivo → chunks eliminados y nuevo índice publicado.  
4. **Archivo inválido**: queda en estado `error`, se reintenta con EventBridge (cron).  
5. **Carga concurrente**: dos archivos al mismo tiempo → índice final consistente.  

---

## ✅ Checklist de implementación

### 🔹 Configuración inicial
- [ ] Crear bucket S3 `workserver-kb` con **versioning ON**.  
- [ ] Definir convención de `canonical_doc_id` (ej. `cliente/carpeta/nombre.pdf`).  
- [ ] Crear parámetro seguro en SSM: `/aws-ia/dev/OPENAI_API_KEY`.  
- [ ] Crear role IAM con permisos mínimos para el Indexer.  

### 🔹 Lambda Indexer
- [ ] Configurar trigger `ObjectCreated` + `ObjectRemoved` en S3.  
- [ ] Implementar extracción de texto y chunking determinista.  
- [ ] Generar embeddings con OpenAI y upsert/delete en vector DB.  
- [ ] Escribir `published_index_version` al final del ciclo.  
- [ ] Publicar métricas básicas en CloudWatch.  

### 🔹 Observabilidad
- [ ] Configurar alarmas en CloudWatch: error sostenido > N min.  
- [ ] Activar EventBridge (cron) para reintentos cada 15 min.  

### 🔹 Pruebas
- [ ] Subir documento válido (crea chunks).  
- [ ] Modificar documento (re-embebe solo delta).  
- [ ] Borrar documento (elimina chunks).  
- [ ] Simular archivo corrupto (registrar error y reintentar).  
- [ ] Subir múltiples archivos simultáneos (consistencia).  

---

## 🚀 Próximos pasos (fuera de esta parte)
- Integrar WhatsApp Webhook → API Gateway → Lambda Chat.  
- Conectar Lambda Chat a la base vectorial publicada.  
- Agregar espejo opcional (Google Drive → S3).  
- Extender métricas y dashboard de administración.  

---

📌 Con esto cerramos la **Parte 1 (S3 + Lambda Indexer)**.  
El siguiente paso será **validar este diseño en arquitectura backend** antes de avanzar al webhook de WhatsApp.  
