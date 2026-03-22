import JSZip from 'jszip';

export interface UnzippedFile {
  name: string;
  buffer: ArrayBuffer;
}

export class ZipHandler {
  static async unzip(file: File): Promise<UnzippedFile[]> {
    const jszip = new JSZip();
    const loaded = await jszip.loadAsync(file);
    const results: UnzippedFile[] = [];

    for (const filename of Object.keys(loaded.files)) {
      const zipEntry = loaded.files[filename];
      if (!zipEntry.dir && filename.match(/\.xls(x)?$/i) && !filename.split('/').pop()?.startsWith('._')) {
        const buf = await zipEntry.async("arraybuffer");
        const simpleName = filename.split('/').pop() || filename;
        results.push({ name: simpleName, buffer: buf });
      }
    }
    return results;
  }
}
