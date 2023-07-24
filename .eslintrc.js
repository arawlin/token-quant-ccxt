module.exports = {
  env: {
    browser: false,
    es2021: true,
    mocha: true,
    node: true,
  },
  extends: ['standard', 'plugin:prettier/recommended', 'plugin:node/recommended'],
  parserOptions: {
    ecmaVersion: 12,
  },
  rules: {
    'node/no-unpublished-require': ['error', { devDependencies: true }],
  },
}
