export default [
  {
    files: ["static/**/*.js"],
    languageOptions: {
      globals: {
        window: "readonly",
        document: "readonly"
      }
    },
    rules: {}
  }
];

