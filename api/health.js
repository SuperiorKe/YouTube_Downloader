export default async (req, res) => {
  res.status(200).json({
    ok: true,
    locked: Boolean(process.env.ACCESS_KEY),
    cookies: Boolean(process.env.YT_COOKIES),
  });
};
