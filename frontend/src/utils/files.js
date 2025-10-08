export const fileToBase64 = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () =>
      resolve(String(reader.result).split(",")[1]); // quita el prefijo data:
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });