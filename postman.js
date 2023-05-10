pm.test("Each object in the response has the required fields and data types", () => {
    const response = pm.response.json();
    pm.expect(response).to.be.an("array");
    response.forEach((obj) => {
            pm.expect(obj.id).to.be.a("number");
            pm.expect(obj.mc, "obj.mc should be a number or null").to.satisfy((value) => { return nullOrNumber(value); });
            pm.test("obj.patient is an object", function () {
                    pm.expect(obj.patient,"obj.patient should be an object, number or null").to.satisfy((value) =>{ return nullOrObject(value) || nullOrNumber(value); });
                    if (typeof obj.patient === "object") {
                            pm.expect(obj.patient.id).to.be.a("number");
                            pm.expect(obj.patient.mc, "obj.patient.mc should be a number or null").to.satisfy((value) => { return nullOrNumber(value); });
                            pm.test("obj.patient.title is an object", function () {
                                    pm.expect(obj.patient.title,"obj.patient.title should be an object, number or null").to.satisfy((value) =>{ return nullOrObject(value) || nullOrNumber(value); });
                                    if (typeof obj.patient.title === "object") {
                                            pm.expect(obj.patient.title.id).to.be.a("number");
                                            pm.expect(obj.patient.title.mc, "obj.patient.title.mc should be a number or null").to.satisfy((value) => { return nullOrNumber(value); });
                                                                                }
                            });
                            pm.expect(obj.patient.firstName, "obj.patient.firstName should be a string or null").to.satisfy((value) => { return nullOrString(value); });                            
                    }
            });
            pm.expect(obj.type, "obj.type should be a string or null").to.satisfy((value) => { return nullOrString(value); });
    });
});
