const path = require('path');

module.exports = {
    entry: './dist/index.js',
    output: {
        filename: 'apt-browser-agent.min.js',
        path: path.resolve(__dirname, 'dist'),
        library: 'APTBrowserAgent',
        libraryTarget: 'umd',
        globalObject: 'this'
    },
    resolve: {
        extensions: ['.js']
    },
    optimization: {
        minimize: true
    }
};
