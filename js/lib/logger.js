const log4js = require('log4js')

require('dotenv').config()
const LOGGER_LEVEL = process.env.LOGGER_LEVEL
console.log('LOGGER_LEVEL', LOGGER_LEVEL)
if (!LOGGER_LEVEL) {
  throw new Error('LOGGER_LEVEL not config')
}

let logger

const init = (name = 'app', useCategory) => {
  const layout = {
    type: 'pattern',
    pattern: `%d{yyyy-MM-dd hh:mm:ss.SSS}${useCategory ? ' %c' : ''} %f{1}:%M:%l %p %m`,
  }
  log4js.configure({
    appenders: {
      console: { type: 'stdout', layout },
      file: { type: 'dateFile', filename: 'logs/' + name + '.log', layout, numBackups: 7, compress: false },
      fileError: { type: 'file', filename: 'logs/' + name + '.error.log', layout, maxLogSize: '20M', backups: 3 },
      filterError: {
        type: 'logLevelFilter',
        appender: 'fileError',
        level: 'error',
      },
    },
    categories: {
      default: { appenders: ['filterError', 'file', 'console'], level: LOGGER_LEVEL, enableCallStack: true },
    },
  })

  logger = log4js.getLogger()
  return logger
}

const shutdown = async () => {
  return new Promise((resolve, reject) => {
    log4js.shutdown((error) => {
      error ? reject(error) : resolve()
    })
  })
}

/**
 * note: must call it after init
 *
 * @param {*} category
 * @returns
 */
const getLogger = (category) => {
  return category ? log4js.getLogger(category) : logger
}

module.exports = {
  init,
  shutdown,
  getLogger,
}
