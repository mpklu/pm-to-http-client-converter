client.test("Each object in the response has the required fields and data types", function() {
    client.assert(Array.isArray(response.body), "response body should be an array");
    response.body.forEach((obj) => {
        client.assert(typeof obj.id === "number", "obj.id should be a number");
        client.assert(nullOrNumber(obj.mc), "obj.mc should be a number or null");
        client.assert(nullOrNumber(obj.patient) || nullOrObject(obj.patient), "obj.patient should be an object, number or null");
        if (typeof obj.patient === "object") {
            client.assert(nullOrNumber(obj.patient.id));
            client.assert(nullOrNumber(obj.patient.mc), "obj.patient.mc should be a number or null");
            client.assert(nullOrNumber(obj.patient.title || nullOrObject(obj.patient).title), "obj.patient should be an object, number or null");
            if (typeof obj.patient.title === "object") {
                client.assert(nullOrNumber(obj.patient.title.id));
                client.assert(nullOrNumber(obj.patient.title.mc), "obj.patient.mc should be a number or null");                
            }
            client.assert(nullOrString(obj.patient.firstName), "obj.patient.firstName should be a string or null");
        }
        client.assert(nullOrString(obj.type), "obj.type should be a string or null").to.satisfy((value) => { return nullOrString(value); });
    });
 })
