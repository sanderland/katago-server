const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const path = require('path');
const { VueLoaderPlugin } = require('vue-loader');
const BundleTracker = require('webpack-bundle-tracker');

module.exports = (env = {}) => {
  const extractCssPlugin = new MiniCssExtractPlugin({
    filename: "[name].css",
    chunkFilename: "[name].[id].css"
  });

  return {
    mode: env.prod ? 'production' : 'development',
    devtool: env.prod ? 'source-map' : 'cheap-module-eval-source-map',
    entry: path.resolve(__dirname, './src/main.ts'),
    output: {
      path: path.resolve(__dirname, './dist'),
      filename: "[chunkhash]/[name].js",
      chunkFilename: "[chunkhash]/[name].[id].js",
      publicPath: "http://127.0.0.1:8000/static/bundles/"
    },
    module: {
      rules: [
        {
          test: /\.vue$/,
          use: 'vue-loader'
        },
        {
          test: /\.ts$/,
          loader: 'ts-loader',
          options: {
            appendTsSuffixTo: [/\.vue$/],
          }
        },
        // Styles
        {
          test: /\.css$/,
          use: [
            MiniCssExtractPlugin.loader,
            {
              loader: "css-loader",
              options: {
                sourceMap: true
              }
            }
          ]
        },
        // Fonts
        {
          test: /\.(eot|otf|ttf|woff|woff2)(\?v=[0-9.]+)?$/,
          loader: "file-loader",
          options: {
            outputPath: "fonts",
            name: "[path][name].[ext]"
          }
        },
        // Images
        {
          test: /\.(png|svg|jpg)(\?v=[0-9.]+)?$/,
          loader: "file-loader",
          options: {
            outputPath: "images",
            name: "[path][name].[ext]"
          }
        }
      ]
    },
    resolve: {
      extensions: ['.ts', '.js', '.vue', '.json'],
      alias: {
        'vue$': 'vue/dist/vue.esm.js'
      }
    },
    plugins: [
      new VueLoaderPlugin(),
      new BundleTracker({
        filename: './webpack-stats.json',
        publicPath: 'http://127.0.0.1:8000/static/bundles/'
      }),
      extractCssPlugin
    ],
  };
}
