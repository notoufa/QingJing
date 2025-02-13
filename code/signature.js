// 用户请求全路径
var requestPath =
  "/api/openapi-icp/inference-api/2128161764802560/aiops-1326615959671779328/test/service/8081//v1/chat/completions";
// 用户ak、sk信息，在移动云控制台获取
var accessKey = "xCwhDX100lhguuXCiEvpXjgAUFAW";
var secretKey = "N0warDpYZUbgAgStcUlqA73vE9FwRH";
var requestMethod = "POST";

//日期格式
Date.prototype.format = function (fmt) {
  var o = {
    "M+": this.getMonth() + 1, //月份
    "d+": this.getDate(), //日
    "h+": this.getHours(), //小时
    "m+": this.getMinutes(), //分
    "s+": this.getSeconds(), //秒
    "q+": Math.floor((this.getMonth() + 3) / 3), //季度
    S: this.getMilliseconds(), //毫秒
  };
  if (/(y+)/.test(fmt)) {
    fmt = fmt.replace(
      RegExp.$1,
      (this.getFullYear() + "").substr(4 - RegExp.$1.length)
    );
  }
  for (var k in o) {
    if (new RegExp("(" + k + ")").test(fmt)) {
      fmt = fmt.replace(
        RegExp.$1,
        RegExp.$1.length == 1 ? o[k] : ("00" + o[k]).substr(("" + o[k]).length)
      );
    }
  }
  return fmt;
};

//生成uuid作为signatureNonce
function uuid() {
  var s = [];
  var hexDigits = "0123456789abcdef";
  for (var i = 0; i < 32; i++) {
    s[i] = hexDigits.substr(Math.floor(Math.random() * 0x10), 1);
  }
  s[14] = "4"; // bits 12-15 of the time_hi_and_version field to 0010
  s[19] = hexDigits.substr((s[19] & 0x3) | 0x8, 1); // bits 6-7 of the clock_seq_hi_and_reserved to 01
  //s[8] = s[13] = s[18] = s[23] = "-";
  var uuid = s.join("");
  return uuid;
}

// var accessKey = pm.environment.get("access_key")
// var secretKey = pm.environment.get("secret_key")

var signatureNonce = uuid();
var signatureVersion = "V2.0";
var signatureMethod = "HmacSHA1";
var timestamp = new Date().format("yyyy-MM-ddThh%3Amm%3AssZ");

var queryString =
  "AccessKey=" +
  accessKey +
  "&SignatureMethod=" +
  signatureMethod +
  "&SignatureNonce=" +
  signatureNonce +
  "&SignatureVersion=" +
  signatureVersion +
  "&Timestamp=" +
  timestamp;
var sha256String = CryptoJS.SHA256(queryString).toString();
requestPath = requestPath.replace(/\//g, "%2F");
var before = requestMethod + "\n" + requestPath + "\n" + sha256String;
print(before);
var signature = CryptoJS.HmacSHA1(
  before,
  "BC_SIGNATURE&" + secretKey
).toString();
pm.environment.set("request_param", queryString + "&Signature=" + signature);
console.log(pm.environment.get("request_param"));
