/** Costat més llarg de la foto que s'envia a l'OCR de la placa. */
const MAX_SIDE = 1600;

export class ImageError extends Error {}

/**
 * Redueix una foto o captura a JPEG ≤ 1600 px i la torna com a data URL.
 * - `imageOrientation: "from-image"` respecta l'orientació EXIF de les fotos del mòbil.
 * - L'OCR de la placa només accepta PNG/JPEG: així sempre li arriba JPEG.
 * - HEIC només es pot llegir a Safari; si el navegador no la sap obrir, es diu clar.
 */
export async function shrinkImage(file: File): Promise<string> {
  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    throw new ImageError("No puc obrir aquesta imatge. Fes servir una foto JPG o PNG.");
  }
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  const width = Math.round(bitmap.width * scale);
  const height = Math.round(bitmap.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (!context) throw new ImageError("Aquest navegador no pot preparar la imatge.");
  // Fons blanc: les captures PNG amb transparència es llegeixen millor.
  context.fillStyle = "#fff";
  context.fillRect(0, 0, width, height);
  context.drawImage(bitmap, 0, 0, width, height);
  bitmap.close();
  return canvas.toDataURL("image/jpeg", 0.85);
}

/** Primera imatge d'un DataTransfer (enganxar o arrossegar). */
export function imageFromTransfer(transfer: DataTransfer | null): File | null {
  if (!transfer) return null;
  for (const item of Array.from(transfer.items ?? [])) {
    if (item.kind === "file" && item.type.startsWith("image/")) {
      const file = item.getAsFile();
      if (file) return file;
    }
  }
  return Array.from(transfer.files ?? []).find((f) => f.type.startsWith("image/")) ?? null;
}
