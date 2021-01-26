module.exports = {
  "*": {
    "secure": false,
    "bypass": (req, res, proxyOptions) => {
      res.setHeader("X-Frame-Options", "SAMEORIGIN");
    }
  }
}