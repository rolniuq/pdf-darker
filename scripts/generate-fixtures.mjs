import * as mupdf from 'mupdf';
import * as fs from 'node:fs';
import * as path from 'node:path';

const fixturesDir = path.resolve(import.meta.dirname, '..', 'tests', 'fixtures');
fs.mkdirSync(fixturesDir, { recursive: true });

function create1PagePDF(filepath) {
  const doc = new mupdf.PDFDocument();
  const buf = new mupdf.Buffer();
  const writer = new mupdf.DocumentWriter(buf, 'pdf', '');

  const device = writer.beginPage([0, 0, 612, 792]);

  const font = new mupdf.Font('Times-Roman');

  // Draw title text
  const titleText = new mupdf.Text();
  titleText.showString(font, [24, 0, 0, 24, 72, 700], 'Hello, Dark Mode!', 0);
  device.fillText(titleText, [1, 0, 0, 1, 0, 0], mupdf.ColorSpace.DeviceRGB, [0, 0, 0], 1.0);
  titleText.destroy();

  // Draw body text
  const bodyText = new mupdf.Text();
  bodyText.showString(font, [12, 0, 0, 12, 72, 650], 'This is a sample PDF document for testing dark mode conversion.', 0);
  device.fillText(bodyText, [1, 0, 0, 1, 0, 0], mupdf.ColorSpace.DeviceRGB, [0.2, 0.2, 0.2], 1.0);
  bodyText.destroy();

  // Draw colored text
  const colorText = new mupdf.Text();
  colorText.showString(font, [14, 0, 0, 14, 72, 600], 'Colored text in blue and red for testing.', 0);
  device.fillText(colorText, [1, 0, 0, 1, 0, 0], mupdf.ColorSpace.DeviceRGB, [0, 0, 0.8], 1.0);
  colorText.destroy();

  // Draw another line
  const line2 = new mupdf.Text();
  line2.showString(font, [12, 0, 0, 12, 72, 550], 'The quick brown fox jumps over the lazy dog. 1234567890', 0);
  device.fillText(line2, [1, 0, 0, 1, 0, 0], mupdf.ColorSpace.DeviceRGB, [0.8, 0, 0], 1.0);
  line2.destroy();

  writer.endPage();
  writer.close();
  font.destroy();

  const pdfBytes = buf.asUint8Array();
  fs.writeFileSync(filepath, Buffer.from(pdfBytes));
  buf.destroy();
  doc.destroy();
  console.log(`Created ${filepath}`);
}

function create3PagePDF(filepath) {
  const doc = new mupdf.PDFDocument();
  const buf = new mupdf.Buffer();
  const writer = new mupdf.DocumentWriter(buf, 'pdf', '');

  const font = new mupdf.Font('Helvetica');

  for (let i = 0; i < 3; i++) {
    const device = writer.beginPage([0, 0, 612, 792]);

    const text = new mupdf.Text();
    text.showString(font, [18, 0, 0, 18, 72, 700], `Page ${i + 1} of 3`, 0);
    device.fillText(text, [1, 0, 0, 1, 0, 0], mupdf.ColorSpace.DeviceRGB, [0, 0, 0], 1.0);
    text.destroy();

    const body = new mupdf.Text();
    body.showString(font, [12, 0, 0, 12, 72, 650], `This is the content of page ${i + 1}. `, 0);
    device.fillText(body, [1, 0, 0, 1, 0, 0], mupdf.ColorSpace.DeviceRGB, [0.3, 0.3, 0.3], 1.0);
    body.destroy();

    writer.endPage();
  }

  writer.close();
  font.destroy();

  const pdfBytes = buf.asUint8Array();
  fs.writeFileSync(filepath, Buffer.from(pdfBytes));
  buf.destroy();
  doc.destroy();
  console.log(`Created ${filepath}`);
}

create1PagePDF(path.join(fixturesDir, 'sample-1page.pdf'));
create3PagePDF(path.join(fixturesDir, 'sample-3page.pdf'));

console.log('All fixtures generated!');
