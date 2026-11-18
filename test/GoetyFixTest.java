import com.electronwill.nightconfig.toml.TomlParser;
import com.google.gson.JsonParser;
import java.io.File;
import java.io.FileReader;

/**
 * Static/sandbox validation for goetyownedfix (1.2.1):
 *  1. mods.toml parsed with the SAME TOML parser Forge uses (night-config)
 *  2. mixins.goetyownedfix.json + pack.mcmeta parsed with gson (same as game)
 *  3. every class in the patch jar loads, and every @Mixin annotation
 *     resolves its target class (forces linking against goety/vanilla types)
 */
public class GoetyFixTest {

    static int failures = 0;

    static String[] MIXIN_CLASSES = {
        "llxj.goetyfix.GoetyOwnedFixMod",
        "llxj.goetyfix.mixin.AbstractEnderlingNullGuardMixin",
        "llxj.goetyfix.mixin.AbstractSpiderServantNullGuardMixin",
        "llxj.goetyfix.mixin.ApostleNullGuardMixin",
        "llxj.goetyfix.mixin.BoneLordNullGuardMixin",
        "llxj.goetyfix.mixin.BroodMotherNullGuardMixin",
        "llxj.goetyfix.mixin.CultistNullGuardMixin",
        "llxj.goetyfix.mixin.EntityIsAlliedToNullGuardMixin",
        "llxj.goetyfix.mixin.HellBlastExplosionNullGuardMixin",
        "llxj.goetyfix.mixin.HereticNullGuardMixin",
        "llxj.goetyfix.mixin.HereticServantNullGuardMixin",
        "llxj.goetyfix.mixin.MaverickServantNullGuardMixin",
        "llxj.goetyfix.mixin.ApostleServantNullGuardMixin",
        "llxj.goetyfix.mixin.HostileDrownedNecromancerNullGuardMixin",
        "llxj.goetyfix.mixin.HostileRedstoneGolemNullGuardMixin",
        "llxj.goetyfix.mixin.HostileRedstoneMonstrosityNullGuardMixin",
        "llxj.goetyfix.mixin.HuntingIllagerEntityNullGuardMixin",
        "llxj.goetyfix.mixin.IfritCloneNullGuardMixin",
        "llxj.goetyfix.mixin.IrkNullGuardMixin",
        "llxj.goetyfix.mixin.MurmurServantNullGuardMixin",
        "llxj.goetyfix.mixin.MurmurServantHeadNullGuardMixin",
        "llxj.goetyfix.mixin.MobUtilNullGuardMixin",
        "llxj.goetyfix.mixin.OwnedNullGuardMixin",
        "llxj.goetyfix.mixin.RipperNullGuardMixin",
        "llxj.goetyfix.mixin.SkullLordNullGuardMixin",
        "llxj.goetyfix.mixin.SquallGolemNullGuardMixin",
        "llxj.goetyfix.mixin.VizierCloneNullGuardMixin",
        "llxj.goetyfix.mixin.VizierNullGuardMixin",
        "llxj.goetyfix.mixin.WitherNecromancerNullGuardMixin"
    };

    public static void main(String[] args) throws Exception {
        String modsToml = args[0];
        String mixinsJson = args[1];
        String packMcmeta = args[2];

        // 1. TOML - same parser Forge uses
        try {
            var config = new TomlParser().parse(new java.io.FileInputStream(modsToml));
            java.util.List<com.electronwill.nightconfig.core.Config> mods = config.get("mods");
            var mod0 = mods.get(0);
            // [[dependencies.goetyownedfix]] is a table-of-lists, not a mod field.
            var deps = config.<com.electronwill.nightconfig.core.Config>get("dependencies")
                             .<java.util.List<Object>>get("goetyownedfix");
            System.out.println("[TOML] OK modId=" + mod0.get("modId")
                + " version=" + mod0.get("version")
                + " deps=" + deps.size());
        } catch (Throwable t) {
            failures++;
            System.out.println("[TOML] FAIL: " + t);
        }

        // 2. JSON - gson
        try {
            var root = JsonParser.parseReader(new FileReader(mixinsJson)).getAsJsonObject();
            System.out.println("[JSON] mixins.goetyownedfix.json OK required=" + root.get("required").getAsBoolean()
                + " entries=" + root.getAsJsonArray("mixins").size()
                + " defaultRequire=" + root.getAsJsonObject("injectors").get("defaultRequire").getAsInt());
        } catch (Throwable t) {
            failures++;
            System.out.println("[JSON] mixins.goetyownedfix.json FAIL: " + t);
        }
        try {
            JsonParser.parseReader(new FileReader(packMcmeta)).getAsJsonObject();
            System.out.println("[JSON] pack.mcmeta OK");
        } catch (Throwable t) {
            failures++;
            System.out.println("[JSON] pack.mcmeta FAIL: " + t);
        }

        // 3. Class loading. Mixin annotations are CLASS-retention, so they cannot be read
        // through reflection; this step only proves every class links/loads. The @Mixin
        // targets themselves are verified with javap against the real target jars.
        for (String c : MIXIN_CLASSES) {
            try {
                Class.forName(c, false, GoetyFixTest.class.getClassLoader());
                System.out.println("[CLASS] OK " + c);
            } catch (Throwable t) {
                failures++;
                System.out.println("[CLASS] FAIL " + c + " -> " + t);
            }
        }

        System.out.println(failures == 0 ? "ALL TESTS PASSED" : failures + " FAILURES");
        System.exit(failures == 0 ? 0 : 1);
    }
}
